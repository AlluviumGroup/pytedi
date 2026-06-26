# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
January 2026

This is the TEDI engine where the timestep calculations are done.

The functions below are only invoked if the user calls the run_model() method in the scenario class.

Calculations moving downstream are easy:
    - Loop through each day
      - Loop through each dam in sequence from upstream to downstream
        - Calculate a water balance for each dam
      - Aggregate for each day
    - Calculate the total catchment outflow at the end of the catchment
    
Calculations moving upstream are harder:
    - Loop through each day
      - Guess the total upstream flow for the day
        - Do the downstream calcs for that single day
        - Check if the calc outflow matches the obs outflow
      - Use a bisection algorithm to choose a revised upstream flow, and repeat
    - Calculate the total catchment outflow at the end of the catchment

@author: robert.morden
"""

import pandas as pd
import numpy as np
from numba import jit
#import time

# %%=======================================================================================================================
'''
This function runs the model.
It starts with pre-processing the data and checking data integrity, then runs either calc_from_up_to_down or calc_from_down_to_up.
'''
def calc_dams(model):
    
    # get model parameters and inputs -----------------------------------------
    damlist_df = model.damlist                                                 
    cat_area = model.cat_area_km2
    scale_limit = model.scale_limit
    
    histoscale_df = model.histoscale.resample('D').interpolate('time')
    if model.timestep == 'month':
        histoscale_df = histoscale_df.resample('MS').first()
    
    
    demand_fields = ~model.ts.columns.isin(['rain', 'evap', 'flowup', 'flowdown'])
    demands_df = model.ts.loc[:,demand_fields]
    
    rain_df = model.ts.loc[:,['rain']]
    evap_df = model.ts.loc[:,['evap']]
    flowin_df = model.ts.loc[:,['flowup']]
    flowout_df = model.ts.loc[:,['flowdown']]
    
    if model.calc_nat_or_obs == 'obs':
        q_df = flowin_df
    elif model.calc_nat_or_obs == 'nat':
        q_df = flowout_df
    
    store_params = {}
    store_params['vary_surfarea'] = model.vary_surfarea
    store_params['vol_surfarea_a'] = model.vol_surfarea_a
    store_params['vol_surfarea_b'] = model.vol_surfarea_b
    store_params['startstore_propfull'] = model.startstore_propfull
    
    # check data integrity ----------------------------------------------------
    # connectivity, catch areas all add up, demand groups all exist in timeseries
    # haven't added this yet, but it could go here
    
    # Clip timeseries to minimum overlapping period
    sdate = max(rain_df.first_valid_index(),evap_df.first_valid_index(),q_df.first_valid_index(),demands_df.first_valid_index(),histoscale_df.first_valid_index())
    edate = min(rain_df.last_valid_index(),evap_df.last_valid_index(),q_df.last_valid_index(),demands_df.last_valid_index(),histoscale_df.last_valid_index())
    
    if edate > sdate:
        rain_df = rain_df.loc[sdate:edate]
        evap_df = evap_df.loc[sdate:edate]
        flowin_df = flowin_df.loc[sdate:edate]
        flowout_df = flowout_df.loc[sdate:edate]
        demands_df = demands_df.loc[sdate:edate,:]
        histoscale_df = histoscale_df.loc[sdate:edate]
    else:
        raise ValueError("Timeseries do not overlap. Check dates in rain, evap, flow, and demand timeseries.")
        
    # run the model -----------------------------------------------------------
    if model.calc_nat_or_obs == 'obs':                                          
        global_results, alldam_results = calc_from_up_to_down(damlist_df, demands_df, rain_df, evap_df, flowin_df, cat_area, scale_limit, histoscale_df, store_params)
    
    elif model.calc_nat_or_obs == 'nat':
        global_results, alldam_results = calc_from_down_to_up(damlist_df, demands_df, rain_df, evap_df, flowout_df, cat_area, scale_limit, histoscale_df, store_params)

    return global_results, alldam_results

# %%=======================================================================================================================
'''
This function will calculate the flow DOWNstream of the dams given the total catchment flow UPstream.
'''
def calc_from_up_to_down(damlist_df, demands_df, rain_df, evap_df, flowin_df, cat_area, scale_limit, histoscale_df, store_params):

    damlist_df = damlist_preprocessing(damlist_df, demands_df, cat_area, scale_limit)
    
    damlist_array = damlist_df.loc[:,['vol_ML','surfacearea_m2','catchuplocal_km2',
                                      'demfactor','year_start','demand_id',
                                      'bypass_MLperT','bypass_start_ddmm','bypass_end_ddmm',
                                      'wfill_MLperT','wfill_start_ddmm','wfill_end_ddmm',
                                      'dsdam','output']].to_numpy(dtype='float64')
    
    # convert timeseries to numpy arrays
    flow_array = flowin_df.to_numpy(dtype='float64').flatten()
    rain_array = rain_df.to_numpy(dtype='float64').flatten()
    evap_array = evap_df.to_numpy(dtype='float64').flatten()
    demd_array = demands_df.to_numpy(dtype='float64')
    
    # create array of year number for each timestep to identify when a dam should activate
    year_array = flowin_df.index.year.to_numpy(dtype='int64')
    mmdd_array = flowin_df.index.strftime('%m%d').astype('int32').to_numpy()
    history_array = histoscale_df.to_numpy(dtype='float64').flatten()
    
    # get start and end of flow series
    
    dtstart = flowin_df.first_valid_index()
    dtend = flowin_df.last_valid_index()
    istart = flowin_df.index.get_loc(dtstart)
    iend = flowin_df.index.get_loc(dtend)
    
    # run calculations
    global_array, alldam_array = tedi_engine_down(flow_array, rain_array, evap_array, demd_array, year_array, mmdd_array, history_array, damlist_array, cat_area, istart, iend,
                                                  store_params['vary_surfarea'], store_params['vol_surfarea_a'], store_params['vol_surfarea_b'], store_params['startstore_propfull'])

    global_results, alldam_results = _format_engine_results(global_array, alldam_array, flowin_df.index)

    return global_results, alldam_results

# %%=======================================================================================================================
@jit (nopython=True, cache=True)
def tedi_engine_down(flow,rain,evap,demd,years,monthday,history,dams,catcharea,istart,iend,varyarea,vsa_a,vsa_b,startprop):

    """
    Calculate farm dam impacts on flow (numba @jit compiled).

    Returns:
        global_array  (nrows, 9)  - catchment fluxes per timestep
        alldam_array  (nrows, n_output, 11) - per-output-dam results per timestep
    where nrows = iend - istart + 1.
    """
    numdams = len(dams)

    n_output = 0                                                               # number of dams flagged for individual output
    for i in range(numdams):
        if dams[i,13] > 0:
            n_output += 1

    nrows = iend - istart + 1
    global_array = np.empty((nrows, 9))
    alldam_array = np.empty((nrows, n_output, 11))

    # set up ENDstore array, set ENDstore = capacity x start proportion
    estore = dams[:,0] * startprop

    for k in range(nrows):                                                     # for each timestep in the useful range
        istep = istart + k
        sstore = estore
        res = stedi_engine_down_singlestep(flow[istep], rain[istep], evap[istep], demd[istep,:],
                                           years[istep], monthday[istep], history[istep],
                                           dams, catcharea, istep, sstore, True, varyarea, vsa_a, vsa_b)
        estore = res[0]
        global_array[k,0] = res[1]; global_array[k,1] = res[2]; global_array[k,2] = res[3]
        global_array[k,3] = res[4]; global_array[k,4] = res[5]; global_array[k,5] = res[6]
        global_array[k,6] = res[7]; global_array[k,7] = res[8]; global_array[k,8] = res[9]
        if n_output > 0:
            alldam_array[k,:,:] = res[10]

    return global_array, alldam_array

# %%=======================================================================================================================
'''
This function will calculate the flow DOWNstream of the dams given the total catchment flow UPstream.
'''
def calc_from_down_to_up(damlist_df, demands_df, rain_df, evap_df, flowout_df, cat_area, scale_limit, histoscale_df, store_params):

    damlist_df = damlist_preprocessing(damlist_df, demands_df, cat_area, scale_limit)
    
    damlist_array = damlist_df.loc[:,['vol_ML','surfacearea_m2','catchuplocal_km2',
                                      'demfactor','year_start','demand_id',
                                      'bypass_MLperT','bypass_start_ddmm','bypass_end_ddmm',
                                      'wfill_MLperT','wfill_start_ddmm','wfill_end_ddmm',
                                      'dsdam','output']].to_numpy(dtype='float64')

    # convert timeseries to numpy arrays
    flow_array = flowout_df.to_numpy().astype('float64').flatten()
    rain_array = rain_df.to_numpy().astype('float64').flatten()
    evap_array = evap_df.to_numpy().astype('float64').flatten()
    demd_array = demands_df.to_numpy(dtype='float64')

    # create array of year number for each timestep to identify when a dam should activate
    year_array = flowout_df.index.year.to_numpy(dtype='int64')
    mmdd_array = flowout_df.index.strftime('%m%d').astype('int32').to_numpy()
    history_array = histoscale_df.to_numpy().flatten()
    
    # get start and end of flow series
    dtstart = flowout_df.first_valid_index()
    dtend = flowout_df.last_valid_index()
    istart = flowout_df.index.get_loc(dtstart)
    iend = flowout_df.index.get_loc(dtend)
    
    # run calculations
    global_array, alldam_array = tedi_engine_up(flow_array, rain_array, evap_array, demd_array, year_array, mmdd_array, history_array, damlist_array, cat_area, istart, iend,
                                                store_params['vary_surfarea'], store_params['vol_surfarea_a'], store_params['vol_surfarea_b'], store_params['startstore_propfull'])

    global_results, alldam_results = _format_engine_results(global_array, alldam_array, flowout_df.index)

    return global_results, alldam_results

# %%=======================================================================================================================
def _format_engine_results(global_array, alldam_array, index):
    '''Turn the engine's numpy result arrays into the catch_results and indiv_results
    DataFrames. global_array is (nsteps, 9); alldam_array is (nsteps, n_output, 11).'''
    global_results_columns = ['sstore', 'flow_up', 'netevap', 'demd_sum', 'wf', 'bp', 'estore', 'flow_down', 'agg_impact']
    global_results = pd.DataFrame(global_array, columns=global_results_columns, index=index)

    alldam_results_columns = ['istep','idam','sstore','local_inflow','updam_spill','netevap','demand','wf','bp','es','outflow']
    alldam_flat = alldam_array.reshape(-1, len(alldam_results_columns))         # (nsteps * n_output, 11)
    alldam_results = pd.DataFrame(alldam_flat, columns=alldam_results_columns)
    alldam_results['istep'] = alldam_results['istep'].astype(int)
    alldam_results['idam'] = alldam_results['idam'].astype(int)
    alldam_results['date'] = alldam_results['istep'].apply(lambda x: index[x])
    columns_order = ['istep', 'idam', 'date', 'sstore', 'local_inflow', 'updam_spill', 'netevap', 'demand', 'wf', 'bp', 'es', 'outflow']
    alldam_results = alldam_results[columns_order]

    return global_results, alldam_results

# %%=======================================================================================================================
'''
This function will calculate the flow UPstream of the dams given the total catchment flow DOWNstream.
This is much harder than calculating the other way, because the flow has to be estimated iteratively.
It includes a bisection solver to estimate the upstream flow.
The original Windows STEDI used a bisection solver, but I'm not sure how it was implemented. This is a new implementation.
'''
@jit (nopython=True, cache=True)
def tedi_engine_up(flow,rain,evap,demd,years,monthday,history,dams,catcharea,istart,iend,varyarea,vsa_a,vsa_b,startprop):
    """
    Calculate flow UPstream of the dams given the catchment flow DOWNstream, using a
    per-timestep bisection solver (numba @jit compiled).

    Returns global_array (nrows, 9) and alldam_array (nrows, n_output, 11), as for
    tedi_engine_down.
    """
    numdams = len(dams)

    n_output = 0
    for i in range(numdams):
        if dams[i,13] > 0:
            n_output += 1

    nrows = iend - istart + 1
    global_array = np.empty((nrows, 9))
    alldam_array = np.empty((nrows, n_output, 11))

    # set up ENDstore array, set ENDstore = capacity x start proportion
    estore = dams[:,0] * startprop

    # set up basic parameters for the bisection
    increment = 2.0
    maxmult = 10.0
    tolerance = 0.02

    outflowcol = 8      # index of the downstream flow (outflow_sum) in the singlestep return tuple

    for k in range(nrows):                                                     # for each timestep in the useful range
        istep = istart + k
        q_obs = flow[istep]                                                    # define the observed downstream flow
        r = rain[istep]
        e = evap[istep]
        d = demd[istep,:]
        mmdd = monthday[istep]
        yy = years[istep]
        h = history[istep]

        sstore = estore

        a = q_obs
        iloop = 0
        maxloops = 10

        res = stedi_engine_down_singlestep(a,r,e,d,yy,mmdd,h,dams,catcharea,istep,sstore,False,varyarea,vsa_a,vsa_b)
        diff_a = res[outflowcol] - q_obs
        b = a
        diff_b = diff_a
        if diff_a < 0:                                                         # if est - obs is negative, the starting flow was too low so we need to increase it
            while (diff_b < 0) and (iloop<maxloops):
                iloop += 1
                b *= increment
                res = stedi_engine_down_singlestep(b,r,e,d,yy,mmdd,h,dams,catcharea,istep,sstore,False,varyarea,vsa_a,vsa_b)
                diff_b = res[outflowcol] - q_obs
            if iloop == maxloops:
                b = a * maxmult
        else:                                                                  # if est - obs is positive, the starting flow was too high so we need to decrease it
            while (diff_b > 0) and (b > tolerance) and (iloop<maxloops):
                iloop += 1
                b /= increment
                res = stedi_engine_down_singlestep(b,r,e,d,yy,mmdd,h,dams,catcharea,istep,sstore,False,varyarea,vsa_a,vsa_b)
                diff_b = res[outflowcol] - q_obs
            if iloop == maxloops:
                b = 0.0

        iloop = 0
        maxloops = 100
        while (abs(b - a) / 2 > tolerance) and (iloop<maxloops):                  # Now that f(a) and f(b) have opposite signs, we can apply the standard bisection algorithm
            iloop += 1
            midpoint = (a + b) / 2
            res = stedi_engine_down_singlestep(midpoint,r,e,d,yy,mmdd,h,dams,catcharea,istep,sstore,False,varyarea,vsa_a,vsa_b)
            diff_mid = res[outflowcol] - q_obs
            if diff_mid == 0:                                                  # We've found an exact root. Cool!
                a = midpoint
                b = midpoint
            elif diff_mid * diff_a < 0:                                        # The root is in the left subinterval
                b = midpoint
            else:                                                              # The root is in the right subinterval
                a = midpoint

        flow_us = (a + b) / 2                                                  # The midpoint is the best estimate of the upstream flow

        res = stedi_engine_down_singlestep(flow_us,r,e,d,yy,mmdd,h,dams,catcharea,istep,sstore,True,varyarea,vsa_a,vsa_b)
        estore = res[0]
        global_array[k,0] = res[1]; global_array[k,1] = res[2]; global_array[k,2] = res[3]
        global_array[k,3] = res[4]; global_array[k,4] = res[5]; global_array[k,5] = res[6]
        global_array[k,6] = res[7]; global_array[k,7] = res[8]; global_array[k,8] = res[9]
        if n_output > 0:
            alldam_array[k,:,:] = res[10]

    return global_array, alldam_array
        
# %%=======================================================================================================================
'''
This function will calculate the flow from up to down for a single timestep.
It needs to be run recursively to find a suitable upstream flow, or can just be run once to find the downstream flow.
'''
@jit (nopython=True, cache=True)
def stedi_engine_down_singlestep(flow,rain,evap,demd,yy,mmdd,history,dams,catcharea,istep,sstore,output_tf,varyarea,a,b):
    
    """
    Calculate farm dam impacts on flow for a SINGLE TIMESTEP
    
    Takes the following inputs:
        flow / rain / evap         (scalar, one row per timestep, all units ML or mm)
        demd                       (1d numpy array, cols = demand for each group)
        yy,mmdd                    (integers, year and month/day)
        history                    (scalar, impact scaling factor from 0 to 1 for all dams)
        dams                       (2d numpy array, 1 row per dam, cols = capacity(ML)/surfarea(m2)/catcharea(km2)/demfactor/buildyear/demandid/bypassrate/bypassstart/bypassend/dsdam/output)
              NOTE that dams includes a dummy dam for the catchment outlet (no capacity, demands, or bypasses)
              The total catchment outflow is the outflow of the dummy dam
        catcharea                  (scalar, size of catchment in km2)
        istep                      (integer, index of timestep in flow/rain/evap/demd arrays)
        sstore                     (1d numpy array, 1 col per dam, cols = start storage for each dam)
    
    Note that all inputs are numpy-based so that NUMBA can make it work super fast
    """
    # set up variables needed for THIS timestep
    numdams = len(dams)
    dsspills = np.zeros(numdams)
    if output_tf:                                                              # only allocate the (per output dam) results when reporting
        dam_results = np.empty((numdams, 11))
    else:
        dam_results = np.empty((0, 11))
    nout = 0

    # set up variables needed for the NEXT timestep
    estore = sstore * 0.0

    # set up AGGREGATE variables for the timestep
    sstore_sum = 0.0
    flow_up_sum = 0.0
    netevap_sum = 0.0
    demd_sum = 0.0
    wf_sum = 0.0
    bp_sum = 0.0
    estore_sum = 0.0
    outflow_sum = 0.0
    aggimpact_sum = 0.0

    for idam in range(0,numdams):                                              # for each dam in the catchment

        ss = sstore[idam]

        capc = dams[idam,0]                                                    # assign dam characteristics and parameters

        if varyarea:
            surf = (ss/a)**(1/b)                                               # surface area varies with volume stored   v = a.s**b  so s = (v/a) ** (1/b)
        else:                                                                  # OR
            surf = dams[idam,1]                                                # surface area is always the maximum

        ctch = dams[idam,2]
        dfac = dams[idam,3]
        buildyr = int(dams[idam,4])
        demdid = int(dams[idam,5])
        bprate = dams[idam,6]
        bpstart = int(dams[idam,7])
        bpend = int(dams[idam,8])
        wfrate = dams[idam,9]
        wfstart = int(dams[idam,10])
        wfend = int(dams[idam,11])
        dsdam = int(dams[idam,12])

        damoutput = False
        if output_tf:
            if dams[idam,13] > 0:
                damoutput = True

        dem = demd[demdid]

        if bpstart<=bpend:                                                     # eg. bypass starts in March and ends in August
            if (mmdd<bpstart) or (mmdd>bpend):                                    # if today is outside the season
                bprate = 0.0                                                      # bypass rate is zero
        else:                                                                  # eg. bypass starts in Nov and ends in May
            if (mmdd<bpstart) and (mmdd>bpend):                                   # if today is outside the season
                bprate = 0.0                                                      # bypass rate is zero

        if wfstart<=wfend:                                                     # eg. wfill starts in March and ends in August
            if (mmdd<wfstart) or (mmdd>wfend):                                    # if today is outside the season
                wfrate = 0.0                                                      # wfill rate is zero
        else:                                                                  # eg. wfill starts in Nov and ends in May
            if (mmdd<wfstart) and (mmdd>wfend):                                   # if today is outside the season
                wfrate = 0.0                                                      # wfill rate is zero

        if yy<buildyr:                                                         # if the build year has not happened yet
            capc = 0.0                                                            # set physical parameters to zero, except catchment area which can remain intact
            surf = 0.0
            ctch = dams[idam,2]
            dfac = 0.0
            ss = 0.0

        # calc inflow, rain, evap, demand, outflows, impact
        localinflow = ctch / catcharea * flow                                  # inflow = damarea / catcharea x flow
        updamspill = dsspills[idam]
        netinflow = localinflow + updamspill - bprate                          # netinflow (make sure bypass flow is taken before demands)
        netevap = surf * (evap-rain) / 1e6                                     # netevap = surface area x netevap / 1e6
        demand = capc * dfac * dem                                             # demand = capacity x demfactor x pattern
        bal = (ss + netinflow - netevap - demand + wfrate)                     # raw water balance

        es = max(0.0, min(bal,capc) )                                          # end storage must be between 0 and capacity
        outflow = max(0.0, bal - es)                                           # outflow = positive, but only if balance exceeds end storage
        if dsdam>=0:                                                           # if the next downstream id is -99, then we are at the end of the catchment
            dsspills[dsdam] = dsspills[dsdam] + outflow + bprate               # outflow directed into another dam

        # aggregate variables across dams as required
        sstore_sum += ss
        flow_up_sum += localinflow
        netevap_sum += netevap
        demd_sum += demand
        bp_sum += bprate
        wf_sum += wfrate
        estore_sum += es
        if idam == numdams-1:
            outflow_sum = outflow
            aggimpact_sum = flow_up_sum - outflow_sum                           # impact = Q-NoDams - Q-WithDams; bypass is already part of outflow_sum, do not subtract again

        # prepare results only if the dam is marked for output
        if damoutput:
            dam_results[nout,0] = istep
            dam_results[nout,1] = idam
            dam_results[nout,2] = ss
            dam_results[nout,3] = localinflow
            dam_results[nout,4] = updamspill
            dam_results[nout,5] = netevap
            dam_results[nout,6] = demand
            dam_results[nout,7] = wfrate
            dam_results[nout,8] = bprate
            dam_results[nout,9] = es
            dam_results[nout,10] = outflow
            nout += 1

        # prepare variables needed for next timestep
        estore[idam] = es                                                      # end storage

    # returns: estore array, then the 9 global fluxes in catch_results column order
    # (sstore, flow_up, netevap, demd_sum, wf, bp, estore, flow_down, agg_impact),
    # then the (n_output, 11) individual-dam results for this timestep
    return (estore, sstore_sum, flow_up_sum, netevap_sum, demd_sum, wf_sum, bp_sum,
            estore_sum, outflow_sum, aggimpact_sum, dam_results[:nout,:])

# %%=======================================================================================================================

def get_us_to_ds_order(df):
    
    reordered_id_list = []
    
    branch_ends = df[~df['dam_id'].isin(df['ds_damid'])]
    branch_junctions = df[df['dam_id'].isin(df['ds_damid'])]
    
    while len(branch_ends)>0:
        reordered_id_list.extend(branch_ends['dam_id'].to_list())
        df = branch_junctions
        branch_ends = df[~df['dam_id'].isin(df['ds_damid'])]
        branch_junctions = df[df['dam_id'].isin(df['ds_damid'])]
        
    return reordered_id_list

# %%=======================================================================================================================

def damlist_preprocessing(damlist_df, demands_df, cat_area, scale_limit):
    
    # determine sum of us areas for selected catchment, adjust if required
    # (ie. the dams cannot impound an area bigger than the total catchment itself, that wouldn't make sense)
    pc_impound = damlist_df['catchuplocal_km2'].sum() / cat_area
    unimp_km2 = cat_area - damlist_df['catchuplocal_km2'].sum()
    if pc_impound > scale_limit:
        damlist_df['catchuplocal_km2'] = damlist_df['catchuplocal_km2'] * (scale_limit/pc_impound)
    
    # sort out the demand groups into integers
    demgroup_mapping = {col_name: i for i, col_name in enumerate(demands_df.columns)}
    damlist_df['demand_id'] = damlist_df['group_name'].map(demgroup_mapping)

    # reorder the dams from upstream to downstream - THIS IS CRITICAL!!!
    new_dam_order = get_us_to_ds_order(damlist_df[['dam_id','ds_damid']])
    damlist_df['dam_id'] = pd.Categorical(damlist_df['dam_id'],categories=new_dam_order,ordered=True)
    damlist_df = damlist_df.sort_values(by='dam_id').reset_index(drop=True)
    damlist_df['dam_id'] = damlist_df['dam_id'].astype('int32')
    
    # sort out the downstream dam ids to be the row index of the downstream dam
    dam_id_to_index = dict(zip(damlist_df['dam_id'], damlist_df.index))
    damlist_df['dsdam'] = damlist_df['ds_damid'].map(dam_id_to_index)
    
    # create new row number to hold the catchment outlet (don't create the row yet)
    new_row_idx = len(damlist_df)

    # Any dams which connect downstream to -99 or any other unknown dam id? Set them equal to the catchment outlet.
    filt = ~damlist_df['dsdam'].isin(damlist_df['dam_id'])           # ds_dam is NOT in dam_id
    damlist_df.loc[filt,'dsdam'] = new_row_idx

    # add a row at the end to represent the catchment outlet
    # need to add [dam_id,      ds_damid, surfarea, catchup,  catchloc,  vol, year, groupname, demfact, bpassQ, bpass_start, bpass_end, wfillQ, wfill_start, wfill_end, output, demandid, dsdam_idx]
    new_row =     [new_row_idx, -99,      0,        cat_area, unimp_km2, 0,   0,    'none',    0,       0,      101,         1231,      0,      101,         1231,      0,      0,        -99]
    damlist_df.loc[new_row_idx] = new_row
    

    return damlist_df

# %%=======================================================================================================================
