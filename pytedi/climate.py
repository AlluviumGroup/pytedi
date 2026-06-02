# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
December 2025

This is the code for importing climate and inflows.
Climate can come from a csv, or a getdat file
Flow can come from a csv, or a getdat file

The logical process is:
    - gather required data (file names, field names, etc)
    - check if the input is a csv, getdat, or dataframe
    - call separate function for each type of input
    
@author: robert.morden
"""

import pandas as pd

# %%=====================================================================================================================
def process_STEDI_climate(params):
    
    fname = params['input_flow_file']
    ifield = params['input_flow_field']
    tstep = params['timestep']
    
    flow = read_STEDI_clim(fname,ifield,tstep)                                 # read the input flow
    
    fname = params['input_rain_file']
    ifield = params['input_rain_field']
    
    rain = read_STEDI_clim(fname,ifield,tstep)                                 # read the input rain
    
    fname = params['input_evap_file']
    ifield = params['input_evap_field']
    
    evap = read_STEDI_clim(fname,ifield,tstep)                                 # read the input evap
    
    clim = pd.DataFrame({'flow':flow,'rain':rain,'evap':evap})                 # combine into a single dataframe
    
    return clim

# %%=====================================================================================================================
def read_STEDI_clim(fname,ifield,tstep):
    '''
    This function reads a fixed width file and gets the 'ifield' column.
    This might be easier with pd.read_fwf, but there could be multiple
    comment characters which read_fwf can't deal with.
    '''
    with open(fname, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if line.startswith('!') or line.startswith('#'):
            pass
        elif not line.startswith('!'):
            data_start_index = i
            break
    
    data_lines = lines[data_start_index:]
    dates = []
    vals = []
    for line in data_lines:
        parts = line.split()
        dates.append(parts[0])
        vals.append(parts[ifield])
    
    if tstep == 'month':
        dates = pd.to_datetime(dates,format='%Y%m')
    elif tstep == 'day':
        dates = pd.to_datetime(dates,format='%Y%m%d')
    
    vals = pd.Series(vals,index=dates)
    
    return vals

# %%=====================================================================================================================
#out = process_STEDI_climate(params)
