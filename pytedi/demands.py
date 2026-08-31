# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
June 2026

This is the code for setting up demand information.
Demands are composed of:
    - a demand factor (proportion of dam that is needed for on-site usage each year), and
    - a demand pattern (proportion of demand that should be applied at each timestep)
    - the pattern is multiplied by the factor
    
Demand factors can be sourced from:
    - the dam list (if the user has provided the field 'dem factor') giving a unique demand factor per dam
    - the demand group (ie. stock and domestic might have a dem factor of 0.5)

Demand patterns can be sourced from:
    - climate data ('smoothed net evap' as used in PRIDE = PET - rainfall, convert to 2 week moving average, then remove negatives)
    - long term pattern from an external file (may need to correct the timestep)
    - a repeating pattern of 12 monthly values
    - patterns are different for each demand group
    
Demand groups are specified:
    - in the dam list (with each dam assigned to a group by the user in the input data)
    - by stepwise linear relationship with volume (eg. vol<5ML are domestic, vol>5ML are irrigation)

All patterns are converted to a long term sequence of values at the correct timestep.
All patterns are then multiplied by the demand factor LATER during run time.

IMPORTANT - It is assumed that the patterns will aggregate to a mean annual value of approximately 1.0.

@author: robert.morden
"""

import pandas as pd
import numpy as np
from .climate import read_STEDI_clim

# %%=====================================================================================================================

def process_STEDI_demands(params,dams,clim):
    
    match params['demand_group_method']:                                       # assign each dam to a demand group with a factor
        
        case 'vol':                                                                # use a volume threshold between groups
            groups, factors = demgroups_byvolume(params,dams)
        
        case 'prob':                                                               # use a probability distribution
            groups, factors = demgroups_byprob(params,dams)
        
        case 'list':                                                               # use a groups specified in a list
            groups, factors = demgroups_bylist(params,dams)
    
    match params['demand_pattern_method']:                                     # assemble a timeseries of demands for each group
        
        case '12m':                                                                # convert a 12 month pattern to a timeseries
            ts = dempatterns_12m(params,clim)
        
        case 'file':                                                               # read a timeseries from a file
            ts = dempatterns_file(params)
        
    return ts, groups, factors    #dataframe (same index as climate), series (same index as damlist), series (same index as damlist)

# %%=====================================================================================================================
'''
This function assigns demand groups based on the dam capacity.
Its assumed there are only 2 demand groups with a single volume threshold between them.
Traditionally, a common assumption is to say that anything smaller than 5ML is stock and domestic, and anything bigger is for irrigation.
The inputs to this routine are the parameters and the dam list.
The function returns a pandas series of the demand groups and demand factors ready to be added to the dam list.
'''
def demgroups_byvolume(params,dams):
    
    # get key parameters
    vol_thresh = params['dem_vol_thresh']
    if params['demand_pattern_method'] == '12m': 
        group_details = params['dem_12m_patterns']
    
    elif params['demand_pattern_method'] == 'file':
        group_details = params['dem_pattern_field_table']
    
    group_names = group_details['Name'].tolist()
    group_factors = group_details['Factor'].tolist()
    
    # set up result list
    groups = pd.Series(index=dams.index,dtype='string')
    factors = pd.Series(index=dams.index,dtype='float32')
    
    # assign
    groups.loc[:] = group_names[0]
    groups = groups.where(dams['vol_ML']<=vol_thresh,other=group_names[1])

    factors.loc[:] = group_factors[0]
    factors = factors.where(dams['vol_ML']<=vol_thresh,other=group_factors[1])

    return groups,factors

# %%=====================================================================================================================
'''
This function assigns demand groups based on a probability distribution.
Its assumed the distribution includes demand group names (eg. Stock and Domestic, or Irrigation).
The group names should correspond with the demand pattern information with a matching factor.
The inputs to this routine are the parameters and the dam list.
The function returns a pandas series of the demand groups and demand factors ready to be added to the dam list.
'''
def demgroups_byprob(params,dams):

    # set up a random number generator
    rng = np.random.default_rng(seed=params.get('seed', 42))

    # get key parameters
    nbins = params['damdist_nrows']
    group_details = params['dem_group_props_per_volbin']
    damdist = params['damdist_table']
    
    groups = pd.Series(index=dams.index)
    factors = pd.Series(index=dams.index)
    
    for ibin in range(nbins):                                                  # for each volume bin
        minvol = damdist.iloc[ibin,1]                                          # get the bin parameters (minvol, maxvol, dem group proportions)
        maxvol = damdist.iloc[ibin,2] 
        group_names = group_details.columns[1:]
        group_probs = group_details.iloc[ibin,1:]
        
        filt = (dams['vol_ml']>=minvol) & (dams['vol_ml']<=maxvol)             # select dams in that bin
        dams_bin = dams[filt]
        ndams = len(dams_bin)
        
        groups[filt] = rng.choice(group_names,size=ndams,p=group_probs)        # generate random numbers and use to assign a group and a factor
    
    group_details = params['dem_pattern_field_table']
    
    group_names = group_details['Name'].tolist()
    group_factors = group_details['Factor'].tolist()
    group_dict = dict(zip(group_names,group_factors))
    
    factors = groups.map(group_dict)                                           # assign demand factors with mapping

    return groups,factors

# %%=====================================================================================================================
'''
This function assigns demand groups based on the dam list.
Its assumed the dam list includes demand groups (eg. Stock and Domestic, or Irrigation) for each dam.
The group names should correspond with the demand pattern information with a matching factor.
The inputs to this routine are the parameters and the dam list.
The function returns a pandas series of the demand groups and demand factors ready to be added to the dam list.
'''
def demgroups_bylist(params,dams):
    
    # get the list
    damlist = params['damlist']
    
    # get the group names
    groups = damlist.loc[1:,'group_name']
    
    # get the factors
    if params['demand_pattern_method'] == '12m': 
        group_details = params['dem_12m_patterns']
    
    elif params['demand_pattern_method'] == 'file':
        group_details = params['dem_pattern_field_table']
    
    group_names = group_details['Name'].tolist()
    group_factors = group_details['Factor'].tolist()
    group_dict = dict(zip(group_names,group_factors))
    
    # assign demand factors with mapping
    factors = groups.map(group_dict)
    
    return groups,factors

# %%=====================================================================================================================
'''
This function assigns demand patterns based on 12 monthly values for each group.
If the timestep is daily, the pattern is disaggregated.
The input is the parameter dictionary.
The output is a DataFrame with a single column per pattern.
'''
def dempatterns_12m(params,clim):
    
    df_12m = params['dem_12m_patterns']
    df_12m = df_12m.set_index('Name', drop=True)                               # reset the index so that the 'Name' column is the index instead of the default integer index
    
    df_12m = df_12m.loc[:, 'Jan':'Dec']                                        # Select only the columns with the monthly values
    df_12m.columns = [1,2,3,4,5,6,7,8,9,10,11,12]                              # Rename the columns to be numeric for easier processing
    df_12m = df_12m.T                                                          # transpose the dataframe so that the months are now rows and the demand groups are columns
    
    start_date = clim.index.min()                                              # Get the start and end dates from the clim dataframe
    end_date = clim.index.max()
    
    if params['timestep'] == 'month':                                          # Create a date range based on the timestep
        date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    elif params['timestep'] == 'day':
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    else:
        raise ValueError("Invalid timestep. Must be 'month' or 'day'.")
    
    df_patt = pd.DataFrame(index=date_range,columns=df_12m.columns)
    
    df_12m.index.name = 'Month'                                                # Ensure the index of df_12m is the month number
    
    df_patt['Month'] = df_patt.index.month                                     # Create a 'Month' column in df_patt based on the index (assuming the index is a datetime)
    
    for column in df_12m.columns:                                              # Loop through each column in df_12m and map the values to df_patt
        if column in df_patt.columns:                                          # Map values based on the 'Month' column
            df_patt[column] = df_patt['Month'].map(df_12m[column])
    
    df_patt.drop(columns=['Month'], inplace=True)                              # Drop the 'Month' column as it's no longer needed

    if params['timestep'] == 'day':                                            # If the timestep is daily, disaggregate the monthly values to daily values
        df_patt = df_patt.apply(lambda x: x / x.index.days_in_month)           # divide each monthly value by the number of days in that month
        
    return df_patt

# %%=====================================================================================================================
'''
This function assigns demand patterns based on an input file.
It is assumed that the input file has the right timestep.
The input is the parameter dictionary.
The output is a DataFrame with a single column per pattern.
'''
def dempatterns_file(params):
    
    fname = params['dem_pattern_file']
    altpath = params['fpath']
    tstep = params['timestep']
    ngroups = params['demand_ngroups']
    field_df = params['dem_pattern_field_table']
    
    patterns = {}
    
    for i in range(ngroups):
        ifield = field_df.iloc[i,1]                                            # get the field number
        group_name = field_df.iloc[i,0]                                        # get the name of the demand (eg. irrigation)
        pattern = read_STEDI_clim(fname,ifield,tstep,altpath)
        patterns[group_name] = pattern
    
    df_patt = pd.DataFrame(patterns,dtype='float64')
    df_patt_transf = transform_patterns(df_patt)
    
    return df_patt_transf

# %%=====================================================================================================================
"""
For each column in df_patt, divide values by that column's mean annual total.

Mean annual total is calculated using only complete calendar years:
- daily data: year must contain every day in that calendar year
- monthly data: year must contain Jan-Dec, with dates at month start
- values must be non-null for the full calendar year

Fallback if no complete valid calendar years exist for a column:
- daily: divide by column.sum() / 365.25
- monthly: divide by column.sum() / 12
"""

def transform_patterns(df_patt):

    # Infer whether daily or monthly
    idx = df_patt.index

    if len(idx) < 2:
        raise ValueError("Need at least two dates to infer daily or monthly frequency")

    if idx.is_month_start.all():
        # Treat as monthly if all timestamps are at the start of a month
        freq = "monthly"
    else:
        # Otherwise assume daily, but check that all timestamps are day-level
        freq = "daily"

    out = df_patt.copy()

    for col in df_patt.columns:
        s = df_patt[col]

        annual_totals = []

        for year, sy in s.groupby(s.index.year):
            sy = sy.sort_index()

            if freq == "daily":
                expected_index = pd.date_range(
                    start=f"{year}-01-01",
                    end=f"{year}-12-31",
                    freq="D",
                )

            elif freq == "monthly":
                expected_index = pd.date_range(
                    start=f"{year}-01-01",
                    end=f"{year}-12-01",
                    freq="MS",
                )

            # Only use whole calendar years with all dates present
            if sy.index.equals(expected_index) and sy.notna().all():
                annual_totals.append(sy.sum())

        if annual_totals:
            divisor = np.mean(annual_totals)
        else:
            if freq == "daily":
                divisor = s.mean(skipna=True) * 365.25
            else:
                divisor = s.mean(skipna=True) * 12

        out[col] = s / divisor

    return out