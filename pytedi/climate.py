# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
June 2026

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
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# %%=====================================================================================================================
def process_STEDI_climate(params):
    
    fname = params['input_flow_file']
    ifield = params['input_flow_field']
    tstep = params['timestep']
    altpath = Path(params['fpath'])
    
    flow = read_STEDI_clim(fname,ifield,tstep,altpath)                                 # read the input flow
    
    fname = params['input_rain_file']
    ifield = params['input_rain_field']
    
    rain = read_STEDI_clim(fname,ifield,tstep,altpath)                                 # read the input rain
    
    fname = params['input_evap_file']
    ifield = params['input_evap_field']
    
    evap = read_STEDI_clim(fname,ifield,tstep,altpath)                                 # read the input evap
    
    clim = pd.DataFrame({'flow':flow,'rain':rain,'evap':evap})                 # combine into a single dataframe
    
    return clim

# %%=====================================================================================================================
def read_STEDI_clim(fname,ifield,tstep,altpath):
    r'''
    This function reads a fixed width file and gets the 'ifield' column.
    This might be easier with pd.read_fwf, but there could be multiple
    comment characters which read_fwf can't deal with.
    
    It is important to check if the file exists.
    Some STEDI scenario files have absolute references like 'C:\data\climate.csv'
    But sometimes they have relative references like 'climate.csv' or 'data\climate.csv'
    
    Assume the file reference is absolute.
    If that doesn't work then add the scenario file path and try again.
    
    '''
    # check if the file exists
    fpath = Path(fname)
    altpath = Path(altpath)
    fileexists = False
    
    if fpath.exists():                                                         # assume absolute file path
        fileexists = True
        f = fname

    elif not fpath.is_absolute():                                              # try adding the scenario file path to it
        fmod = altpath / fpath
        if fmod.exists():
            fileexists = True
            f = str(fmod)

    if not fileexists:                                                         # dead absolute path (eg. former 'S:\...' drive)?
        fmod = altpath / fpath.name                                           # fall back to <scenario dir>/<basename>
        if fmod.exists():
            fileexists = True
            f = str(fmod)
            logger.warning('Input file not found at "%s"; inferring "%s" from the scenario directory instead.', fname, f)
            
    # if the file exists, go ahead and process it
    if fileexists:
        with open(f, 'r') as file:
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
    
    # if the file does not exist, return an error and stop
    else:
        logger.info('Climate file does not exist: %s', fname)
        raise IOError(f'Climate file does not exist: {fname}')
        
    return vals

# %%=====================================================================================================================

