# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
November 2026

This is the code for setting up bypasses and other related functions.

Bypasses can either operate from:
    - a given start date to an end date, or
    - all year round.

Start and end dates can be specific to the dam or global.

Bypasses have a set flow capacity, eg 0.1 ML per day. That value can be determined by:
    - a value given in the original dam list, or
    - a catchment wide value (eg. 0.1 ML per day per sq.km.) which is then multiplied
      by the dam catchment to get a bypass capacity for a specific dam.

Winterfill pumping is a similar issue:
    - start and end dates can be individual or global
    - pump rates can be individual or global
    
Other features which should appear here but have not been implemented include:
    - seepage through the dam wall and into the ground
    - flows returning to the dam (ie. re-use dams)
    - flows returning to the stream (ie. irrigation returns)
    THESE FEATURES WILL APPEAR IN FUTURE VERSIONS IF THERE IS A NEED.

@author: robert.morden
"""

import pandas as pd

#%%=====================================================================================================================

def process_STEDI_bypasses(params,dams):
    
    bpass = STEDI_bypasses(params,dams)
    
    wfill = STEDI_winterfill(params,dams)
    
    return bpass, wfill

#%%=====================================================================================================================
'''
This function determines the bypass details for each dam.
Start and end dates are global.
There are multiple ways of determining the flowrate.
Inputs are parameters and dam list.
Output is a dataframe specifying the bypass flowrate, bypass startdate, bypass enddate for each dam.
'''
def STEDI_bypasses(params,dams):
    rate = []
    sdate = []
    edate = []
    
    if 'bypass_MLperTperKM2' in params.keys():                                 # if there is a global bypass rate per km2
        rateperkm2 = params['bypass_MLperTperKM2']
        for damarea in dams['catchuptotal_km2']:
            rate.append(damarea * rateperkm2)
        for dam in dams['dam_id']:
            sdate.append(params['bypass_start_mmdd'])
            edate.append(params['bypass_end_mmdd'])
    
    
    elif 'dam_list_inc_bypass' in params.keys():
        if params['dam_list_inc_bypass']:                                        # if the bypass rate is given in a list
            rate = dams['bypass_MLperT'].to_list()
            for dam in dams['dam_id']:
                sdate.append(params['bypass_start_mmdd'])
                edate.append(params['bypass_end_mmdd'])
        else:                                                                      # otherwise set bypass rates to zero
            for dam in dams['dam_id']:
                rate.append(0.0)
                sdate.append(101)
                edate.append(1231)
    else:                                                                      # otherwise set bypass rates to zero
        for dam in dams['dam_id']:
            rate.append(0.0)
            sdate.append(101)
            edate.append(1231)
    
    rate = pd.Series(rate, index=dams.index)                                   # convert to a series
    sdate = pd.Series(sdate, index=dams.index)
    edate = pd.Series(edate, index=dams.index)
    
    if 'bypass_minvol' in params.keys():                                       # filter if below min volume
        minvol = params['bypass_minvol']
        filt = dams['vol_ML'] <= minvol
        rate.loc[filt] = 0.0
        
    if 'bypass_mincatch' in params.keys():                                     # filter if below min total upstream catch
        minarea = params['bypass_mincatch']
        filt = dams['catchuptotal_km2'] <= minarea
        rate.loc[filt] = 0.0
        
    bpass = pd.DataFrame({'bypass_MLperT':rate,'bypass_start_mmdd':sdate,'bypass_end_mmdd':edate})
    
    return bpass
#%%=====================================================================================================================
'''
This function determines the winterfill details for each dam.
Start and end dates are global.
There are multiple ways of determining the flowrate.
Inputs are parameters and dam list.
Output is a dataframe specifying the winterfill flowrate, winterfill startdate, winterfill enddate for each dam.
'''
def STEDI_winterfill(params,dams):
    rate = []
    sdate = []
    edate = []
    
    
    if 'dam_list_inc_wfill' in params.keys():
        if params['dam_list_inc_wfill']:                                           # if the wfill rate is given in a list
            rate = dams['wfill_MLperT'].to_list()
            for dam in dams['dam_id']:
                sdate.append(params['wfill_start_mmdd'])
                edate.append(params['wfill_end_mmdd'])
        
        else:                                                                      # otherwise set wfill rates to zero
            for dam in dams['dam_id']:
                rate.append(0.0)
                sdate.append(101)
                edate.append(1231)
    else:                                                                      # otherwise set wfill rates to zero
        for dam in dams['dam_id']:
            rate.append(0.0)
            sdate.append(101)
            edate.append(1231)
            
    rate = pd.Series(rate, index=dams.index)                                   # convert to a series
    sdate = pd.Series(sdate, index=dams.index)
    edate = pd.Series(edate, index=dams.index)
            
    wfill = pd.DataFrame({'wfill_MLperT':rate,'wfill_start_mmdd':sdate,'wfill_end_mmdd':edate})

    return wfill