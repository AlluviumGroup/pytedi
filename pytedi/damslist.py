# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
June 2026

This is where a list of dams is developed based on input data.
Inputs could be a straightforward dataframe, or an old STEDI scenario file.

@author: robert.morden
"""

import pandas as pd
import numpy as np

# %%=====================================================================================================================
def process_STEDI_dams(params):

    if params['dam_dist_or_list'] == 'list':                                   # if its a list...
        damlist = damlist_from_list(params)                                    # run the creation subroutine with the name of the file containing the list and a dictionary of field names
        
    elif params['dam_dist_or_list'] == 'dist':                                 # if its a distribution...
        damlist = damlist_from_distribution(params)                            # run the creation subroutine with the distribution data
    
    return damlist

# %%=====================================================================================================================
def damlist_from_list(params):
    
    '''
    This function creates a list of dams from list provided by a windows STEDI scenario file.
    Note this is a PURE list of DAMS ONLY. The outlet is removed because its not really a dam.
    
    Parameters
    ----------
    params : dictionary
        Consolidated information from the scenario file.
        In particular, the following are required:
            - cat_area_km2
            - total_dam_vol_ML
            - vol_surfarea_a
            - vol_surfarea_b
            - dam_list_inc_network
            - damlist (dataframe with the following fields...)
                - dam_id
                - ds_dam_id         (optional here, only if dam_list_inc_network = True)
                - surfacearea_m2
                - vol_ML
                - catchuptotal_km2
                - group_name        (not necessary here, only populated if dam_list_inc_demgroups=True)
                - wfill_MLperT      (not necessary here, only populated if dam_list_inc_wfill=True)
                - bypass_MLperT     (not necessary here, only populated if dam_list_inc_bypass=True)

    Returns
    -------
    damlist : dataframe
        List of dams in a dataframe.
        The fields in the dataframe include:
            - dam_id
            - ds_damid
            - surfacearea_m2
            - vol_ML
            - bypass_MLperT  (not filled in here)
            - wfill_MLperT  (not filled in here)
            - catchuptotal_km2
            - catchuplocal_km2
            
    '''
    
    damlist = params['damlist']                                                # grab the dataframe from the STEDI scenario file (columns already correct)
    
    # In a STEDI file, dam # 1 is always the catchment outlet -> REMOVE IT - we only want a list of actual dams
    filt = damlist['dam_id']!=1                                                # filter to exclude the outlet
    damlist = damlist.loc[filt,:].copy()                                       # remove the outlet from the list (It gets added back later as part of dam pre-processing)
    
    filt = damlist['ds_damid'] == 1                                            # identify all dams which flow directly to the outlet
    damlist.loc[filt,'ds_damid'] = -99                                         # set their ds dam to -99 (because we just removed the outlet node, we will put it back later)
    
    if params['dam_list_inc_network']:
        if not 'catchuplocal_km2' in damlist:                                      # calculate interstation areas if not already present
            damlist['catchuplocal_km2'] = np.nan
            
            for index, row in damlist.iterrows():                                  # Iterate through each dam and calculate the local upstream area
                damid = row['dam_id']
                a_tot = row['catchuptotal_km2']
                
                us_dams = damlist[damlist['ds_damid'] == damid]                    # Find dams that have a ds damid matching the current damid
                us_area_sum = us_dams['catchuptotal_km2'].sum()                    # Calculate the sum of the areas of the upstream dams
                
                a_loc = a_tot - us_area_sum                                        # Calculate the local upstream area
                
                damlist.loc[index, 'catchuplocal_km2'] = a_loc                      # Update the local upstream area in the dataframe
    else:
        damlist.loc[:,'catchuplocal_km2'] = damlist['catchuptotal_km2']                  # set LOCAL equal to TOTAL UPSTREAM
    
    # total_area = params['cat_area_km2']                                        # check total catchment area
    # scale_limit = params['scale_limit']
    # total_dam_catch = damlist['catchuplocal_km2'].sum()                        # sum of local catchments of dams, EXCLUDING OUTLET
    
    # if total_dam_catch > (total_area*scale_limit):
    #     factor = (total_area*scale_limit) / total_dam_catch
    #     damlist['catchuplocal_km2'] = damlist['catchuplocal_km2'] * factor
    #     damlist['catchuptotal_km2'] = damlist['catchuptotal_km2'] * factor
    
    return damlist
    
# %%=====================================================================================================================
def damlist_from_distribution(params):
    
    '''
    This function creates a list of dams from distribution provided by a windows STEDI scenario file.
    Note this is a PURE list of DAMS ONLY. The outlet is not created here because its not really a dam.
    
    Parameters
    ----------
    params : dictionary
        Consolidated information from the scenario file.
        In particular, the following are required:
            - cat_area_km2
            - total_dam_vol_ML
            - vol_surfarea_a
            - vol_surfarea_b
            - damdist_nrows
            - damdist_table
            - damcatch_method
            - damcatch_table

    Returns
    -------
    damlist : dataframe
        List of dams in a dataframe.
        The fields in the dataframe include:
            - dam_id
            - ds_damid
            - surfacearea_m2
            - vol_ML
            - bypass_MLperT  (not filled in here)
            - wfill_MLperT  (not filled in here)
            - catchuptotal_km2
            - catchuplocal_km2
    '''

    # get key parameters
    targetvol = params['total_dam_vol_ML']
    aa = params['vol_surfarea_a']
    bb = params['vol_surfarea_b']
    catcharea_method = params['damcatch_method']
    
    # set up the distribution of dam volumes
    vol_low = (params['damdist_table'])['vol_low']                                  # These are the lower bounds of each bin in the histogram
    vol_high = (params['damdist_table'])['vol_high']                                # These are the upper bounds of each bin in the histogram
    vol_prob = (params['damdist_table'])['vol_prob']                                # These are the probabilities for each bin in the histogram
    
    # set up the list dataframe
    damlist = pd.DataFrame(columns=['dam_id'])
    #damlist.set_index('dam_id',inplace=True)
    
    # set up a random number generator
    rng = np.random.default_rng(seed=42)
    
    # generate dams until the total volume exceeds the assigned total
    sumvol = 0.0
    sampled_values = []
    
    while sumvol < targetvol:
        chosen_bin = rng.choice(len(vol_prob), p=vol_prob)                     # Choose a bin based on the defined probabilities
        sampled_value = rng.uniform(vol_low[chosen_bin], vol_high[chosen_bin]) # Sample a value uniformly from the chosen bin
        sampled_values.append(sampled_value)                                   # Add the sampled value to the list and update the current sum
        sumvol += sampled_value
        
        if sumvol > targetvol:                                                 # But what if the last dam is a whopper and we exceed the target by a huge amount? This actually happened on the first test! The target was 800, the last dam was 50ML!
            median_dam_vol = np.median(sampled_values)
            while sumvol > targetvol + median_dam_vol:                         # Check excess volume compared to a typical dam. If we compare by percentage, we might never land a solution.
                removed_value = sampled_values.pop()                           # Remove the last sampled value
                sumvol -= removed_value                                        # Update the total volume by subtracting the removed value

    damlist['vol_ML'] = sampled_values
    
    # generate surface areas
    # volume = A x surfarea^B
    # surfarea = (volume / A)^(1/B)
    damlist['surfacearea_m2'] = (damlist['vol_ML']/aa)**(1/bb)
    
    # generate catchment areas - this requires a separate routine. Need to specify in the params whether this is randomly assigned (Morden 2018), or linearly assigned (Nathan 2004).
    if catcharea_method == 'random':
        catch_areas = catch_areas_random(damlist['vol_ML'],params)
        
    elif catcharea_method == 'linear':
        catch_areas = catch_areas_linear(damlist['vol_ML'],params)
    
    damlist['catchuptotal_km2'] = catch_areas
    damlist['catchuplocal_km2'] = catch_areas
    
    # generate downstream dam ids
    damlist['dam_id'] = damlist.index + 1
    damlist['ds_damid'] = int(-99)
    
    # return the list
    return damlist

# %%=====================================================================================================================
'''
This routine creates catchment areas for each dam based on:
    - the volume of the dam,
    - a series of volume categories with and high and low bounds, and
    - mean and standard deviation for a lognormal distribution of catchment areas in each volume category.
If the total catchment area is in excess of 80% of the total catchment, they are all linearly scaled down accordingly.
'''
def catch_areas_random(volumes,params):

    # get key parameters
    vol_max = (params['damcatch_table'])['vol_max']
    area_mean = (params['damcatch_table'])['area_mean_lognorm']
    area_sd = (params['damcatch_table'])['area_sd_lognorm']
    scale_limit = params['scale_limit']
    total_area = params['cat_area_km2']
    
    # set up a random number generator
    rng = np.random.default_rng(seed=42)
    
    # set up result list
    catch_areas = volumes * 0.0
    
    # Determine the bin for each volume, assign the mean and sd and a random number, then calculate area
    catch_areas['volumes'] = volumes
    catch_areas['bin'] = np.searchsorted(vol_max, catch_areas['volumes'], side='right')
    catch_areas['mean'] = catch_areas['bin'].apply(lambda x: area_mean[x])
    catch_areas['sd'] = catch_areas['bin'].apply(lambda x: area_sd[x])
    #catch_areas['rand'] = rng.uniform[0,1]
    catch_areas['area'] = rng.lognormal(mean=catch_areas['mean'], sigma=catch_areas['sd'])
    
    if catch_areas['area'].sum() > (total_area*scale_limit):
        factor = (total_area*scale_limit) / catch_areas['area'].sum()
        catch_areas['area'] = catch_areas['area'] * factor
        
    return catch_areas['area']
    
# %%=====================================================================================================================
'''
This routine creates catchment areas for each dam based on:
    - the volume of the dam,
    - a stepwise linear relationship between volume and area.
If the total catchment area is in excess of 80% of the total catchment, they are all linearly scaled down accordingly.
'''
def catch_areas_linear(volumes,params):

    # get key parameters
    vol_max = (params['damcatch_table'])['vol_max']
    area_max = (params['damcatch_table'])['area_max']
    total_area = params['cat_area_km2']
    
    if 'scale_limit' in params.keys():
        scale_limit = params['scale_limit']
    else:
        scale_limit = 0.8
    
    # check that the first entry in the stepwise relationship is 0,0
    if vol_max[0] > 0.0:
        vol_max.insert(0,0.0)
        area_max.insert(0,0.0)
    
    # set up result list
    catch_areas = volumes * 0.0

    # interpolate the stepwise relationship
    catch_areas['volumes'] = volumes
    catch_areas['area'] = stepwise_lin_interp(volumes,vol_max,area_max)

    if catch_areas['area'].sum() > (total_area*scale_limit):
        factor = (total_area*scale_limit) / catch_areas['area'].sum()
        catch_areas['area'] = catch_areas['area'] * factor

    return catch_areas['area']
    
# %%=====================================================================================================================
'''
This routine does linear interpolation of a stepwise relationship.
For example, if the relationship between volume and surface area is (0,0), (5,0.5), (100,1.2)
then this function will interpolate as needed.
Values in excess of the max xp are extrapolated from the last two points.
'''
def stepwise_lin_interp(x, xp, fp):
    x = np.asarray(x)
    xp = np.asarray(xp)
    fp = np.asarray(fp)
    
    # Create an array to hold the results
    result = np.empty_like(x, dtype=float)
    
    # Interpolate for values within the range
    mask = x <= xp[-1]
    result[mask] = np.interp(x[mask], xp, fp)
    
    # Extrapolate for values beyond the range
    mask = x > xp[-1]
    slope = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2])
    result[mask] = fp[-1] + slope * (x[mask] - xp[-1])
    
    return result

