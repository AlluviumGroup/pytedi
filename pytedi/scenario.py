"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
October 2025

These are the routines for converting old windows scenario files.
Users can convert old windows STEDI and TEDI files for use with pyTEDI.
    
@author: robert.morden
"""

import pandas as pd
import numpy as np
import os

# %%=====================================================================================================================
def read_scenario_file(scenfile):
    
    # check what sort of scenario file it is
    scenfile_type = ''
    
    # read the second line
    # if the line is 'STEDI  Version 1.' then thats an old windows STEDI scenario, from v1.00 up to v1.24.
    # if the line is 
    # if the line is anything else, file type not recognised. Give a warning.
    with open(scenfile, encoding='latin-1') as stream:
        line1 = stream.readline()
        line2 = stream.readline()
        if line2[:17] == 'STEDI  Version 1.':
            scenfile_type = 'STEDI'
        else:
            scenfile_type = 'unknown'
            raise IOError(f"The input file is not a known TEDI or STEDI scenario format./n{scenfile}")
    
    if scenfile_type == 'STEDI':
        params = read_scenario_winstedi_v1(scenfile)

    if scenfile_type == 'TEDI':
        params = read_scenario_oldtedi_v1(scenfile)
    
    return params

# %%=====================================================================================================================
def read_scenario_winstedi_v1(scenfile):
    '''
    This function reads a windows STEDI scenario file.
    It converts the contents into a dictionary that can then be used by other subroutines
    to develop the inputs required for pytedi.
    The output of this function is a dictionary.
    
    Parameters
    ----------
    scenfile : string
        Full path and file name of the scenario file (.scn).

    Returns
    -------
    params : dictionary
        Consolidated information from the scenario file.

    '''
    params = {}
    params['fname'] = os.path.basename(scenfile)
    params['fpath'] = os.path.dirname(scenfile)
    
    with open(scenfile, encoding='latin-1') as stream:
        for line in stream:
            
            match line.strip().lower():
                
                case "scenario title:":
                    params['title'] = next(stream).strip()
                
                case "calculation timestep:":
                    txt1 = next(stream).strip().lower()
                    if txt1 == 'daily':
                        params['timestep'] = 'day'
                    elif txt1 == 'monthly':
                        params['timestep'] = 'month'
                    else:
                        raise IOError(f"ERROR - The scenario uses a {txt1} timestep which is not compatible with pytedi.")
                
                case "calculation method - calculate natural given observed?:":
                    txt1 = next(stream).strip().lower()
                    if txt1 == 'true':
                        params['calc_nat_or_obs'] = 'nat'
                    else:
                        params['calc_nat_or_obs'] = 'obs'
                    
                case "catchment area (km²):":
                    txt1 = next(stream).strip().lower()
                    params['cat_area_km2'] = float(txt1)
                    
                case "input flow file:":
                    txt1 = next(stream).strip()
                    txt2 = next(stream).strip()
                    params['input_flow_file'] = txt1
                    params['input_flow_field'] = int(txt2)
                    
                case "rainfall file:":
                    txt1 = next(stream).strip()
                    txt2 = next(stream).strip()
                    params['input_rain_file'] = txt1
                    params['input_rain_field'] = int(txt2)
                    
                case "evaporation file:":
                    txt1 = next(stream).strip()
                    txt2 = next(stream).strip()
                    params['input_evap_file'] = txt1
                    params['input_evap_field'] = int(txt2)
                    
                case "enter details of each dam individually?:":
                    txt1 = next(stream).strip().lower()
                    if txt1 == 'true':
                        params['dam_dist_or_list'] = 'list'
                    else:
                        params['dam_dist_or_list'] = 'dist'
                    
                case "total volume of farm dams in catchment (ml):":
                    txt1 = next(stream).strip()
                    params['total_dam_vol_ML'] = float(txt1)
                    
                case "distribution of farm dam volumes:":
                    txt1 = next(stream).strip()
                    txt2 = next(stream).strip()
                    nbins = int(txt1)
                    params['damdist_nrows'] = nbins
                    
                    # Initialize lists to store the data
                    vol_classes = []
                    lower = []
                    upper = []
                    props = []
                    
                    # Read the data lines
                    for _ in range(nbins):
                        line = next(stream).strip()
                        parts = line.split()
                        vol_classes.append(int(parts[0]))
                        lower.append(float(parts[1]))
                        upper.append(float(parts[2]))
                        props.append(float(parts[3]))

                    # Create a dataframe from the collected data
                    params['damdist_table'] = pd.DataFrame({'id': vol_classes,
                                                            'vol_low': lower,
                                                            'vol_high': upper,
                                                            'vol_prob': props})
                    
                case "a:":
                    txt1 = next(stream).strip()
                    params['vol_surfarea_a'] = float(txt1)
                    
                case "b:":
                    txt1 = next(stream).strip()
                    params['vol_surfarea_b'] = float(txt1)
                    
                case "volume catchment area relationship:":
                    txt1 = next(stream).strip()
                    txt2 = next(stream).strip()
                    nbins = int(txt1)
                    
                    # Initialize lists to store the data
                    vols = []
                    areas = []
                    
                    # Read the data lines
                    for _ in range(nbins):
                        line = next(stream).strip()
                        parts = line.split()
                        vols.append(float(parts[0]))
                        areas.append(float(parts[1]))

                    # Create a dataframe from the collected data
                    params['damcatch_table'] = pd.DataFrame({'vol_max': vols, 'area_max': areas})
                    params['damcatch_method'] = 'linear'
                                       
                case "number of demand groups:":
                    txt1 = next(stream).strip()
                    params['demand_ngroups'] = int(txt1)
                    
                case "employ volume threshold between demand groups:":
                    txt1 = next(stream).strip().lower()
                    if txt1 == 'true':
                        params['demand_group_method'] = 'vol'
                    else:
                        params['demand_group_method'] = 'prob'                    #<<<<< Complex linkages to list or dist. Need to review.
                    
                case "threshold volume (ml):":
                    txt1 = next(stream).strip()
                    params['dem_vol_thresh'] = float(txt1)
                    
                case "monthly demand details:":
                    params['demand_pattern_method'] = '12m'
                    txt1 = next(stream).strip()
                    nbins = params['demand_ngroups']
                    
                    # Initialize lists to store the data
                    name = []
                    factor = []
                    months = {month: [] for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
                    
                    # Read the data lines
                    for _ in range(nbins):
                        line = next(stream).strip()
                        parts = line.split()
                        name.append(str(parts[0]))
                        factor.append(float(parts[1]))
                        for i, month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                            months[month].append(float(parts[i + 2]))

                    # Create a dataframe from the collected data
                    params['dem_12m_patterns'] = pd.DataFrame({'Name': name, 'Factor': factor, **months})
                    
                case "proportion of demand groups in each volume class:":
                    params['demand_group_method'] = 'prob'
                    txt1 = next(stream).strip()
                    txt2 = next(stream).strip()
                    nbins = params['demand_ngroups']
                    ncols = params['damdist_nrows']

                    # Initialize lists to store the data
                    name = []
                    props = {col: [] for col in range(ncols)}
                    
                    # Read the data lines
                    for _ in range(nbins):
                        line = next(stream).strip()
                        parts = line.split()
                        name.append(str(parts[0]))
                        for i in range(ncols):
                            props[i].append(float(parts[i + 1]))

                    # Create a dataframe from the collected data
                    params['dem_group_props_per_volbin'] = pd.DataFrame({'Name': name, **props})
                    
                case "demand timeseries input file:":
                    params['demand_pattern_method'] = 'file'
                    txt1 = next(stream).strip()
                    params['dem_pattern_file'] = str(txt1)
                    
                case "demand timeseries details:":
                    txt1 = next(stream).strip()
                    nbins = params['demand_ngroups']

                    # Initialize lists to store the data
                    name = []
                    fieldnum = []
                    factor = []
                    
                    # Read the data lines
                    for _ in range(nbins):
                        line = next(stream).strip()
                        parts = line.split()
                        name.append(str(parts[0]))
                        fieldnum.append(int(parts[1]))
                        factor.append(float(parts[2]))

                    # Create a dataframe from the collected data
                    params['dem_pattern_field_table'] = pd.DataFrame({'Name': name, 'fieldnum': fieldnum, 'Factor': factor})
                    
                case "exponent of flow-area relationship:":
                    txt1 = next(stream).strip()
                    params['flow_area_exp'] = float(txt1)
                    
                case "rate for low flow bypass capacity in ml/d/km2:":
                    txt1 = next(stream).strip()
                    params['bypass_MLperTperKM2'] = float(txt1)
                    
                case "bypass override - turn low flow bypasses on for all dams bigger than capacity in ml:":
                    txt1 = next(stream).strip()
                    params['bypass_minvol'] = float(txt1)
                    
                case "bypass override - turn low flow bypasses on for all dams on catchments larger than area in km2:":
                    txt1 = next(stream).strip()
                    params['bypass_mincatch'] = float(txt1)
                    
                case "period for which bypasses are active (start/end mmdd mmdd):":
                    txt1 = next(stream).strip()
                    parts = txt1.split()
                    params['bypass_start_mmdd'] = int(parts[0])
                    params['bypass_end_mmdd'] = int(parts[1])
                    
                case "adopt maximum dam surface area for climate calculations?:":
                    pass
                    
                case "starting storage volumes (% full):":
                    txt1 = next(stream).strip()
                    params['sstore_pc'] = float(txt1)
                                       
                case "individual dam details:":
                    reading_dam_details = True
                    params['dam_dist_or_list'] = 'list'
                    while reading_dam_details:
                        line = next(stream).strip()
                        match line[:30].strip().lower():                             # only read the first 30 characters - lots of data on the same line
                            
                            case 'multiple demand groups?':
                                txt1 = line[40:].strip().lower()
                                if txt1 == 'true':
                                    params['dam_list_inc_demgroups'] = True
                                    params['demand_group_method'] = 'list'
                                else:
                                    params['dam_list_inc_demgroups'] = False
                                
                                
                            case 'multiple results groups?':
                                pass                                
                            
                            case 'winterfill pumping?':
                                txt1 = line[40:]
                                parts = txt1.split()
                                if parts[0] == 'true':
                                    params['dam_list_inc_wfill'] = True
                                else:
                                    params['dam_list_inc_wfill'] = False
                                params['wfill_start_mmdd'] = int(parts[1])
                                params['wfill_end_mmdd'] = int(parts[2])
                                
                            case 'low flow bypasses?':
                                txt1 = line[40:]
                                parts = txt1.split()
                                if parts[0] == 'true':
                                    params['dam_list_inc_bypass'] = True
                                else:
                                    params['dam_list_inc_bypass'] = False
                                params['bypass_start_mmdd'] = int(parts[1])
                                params['bypass_end_mmdd'] = int(parts[2])
                                
                            case 'spatial networking?':
                                txt1 = line[40:]
                                if txt1 == 'true':
                                    params['dam_list_inc_network'] = True
                                else:
                                    params['dam_list_inc_network'] = False
                                
                            case 'seepage losses?':
                                pass
                                
                            case 'dam details:':
                                reading_dam_details = False                      # stop reading dam details after this section
                                
                                txt1 = next(stream).strip()
                                txt2 = next(stream).strip()
                                txt2 = next(stream).strip()
                                ndams = int(txt1)
                                
                                # Initialize lists to store the data
                                damid = []
                                sa = []
                                vol = []
                                ca = []
                                demgroup = []
                                wfill = []
                                bypass = []
                                ds_damid = []
                                
                                # Read the data lines
                                for _ in range(ndams):
                                    line = next(stream).strip()
                                    parts = line.split()
                                    damid.append(int(parts[0]))
                                    sa.append(float(parts[1]))
                                    vol.append(float(parts[2]))
                                    ca.append(float(parts[3]))
                                    demgroup.append(str(parts[4]))
                                    # NOT READING RESULTS GROUP
                                    wfill.append(float(parts[6]))
                                    bypass.append(float(parts[7]))
                                    ds_damid.append(int(parts[8]))
            
                                # Create a dataframe from the collected data
                                params['damlist'] = pd.DataFrame({'dam_id': damid,
                                                                  'ds_dam_id': ds_damid,
                                                                  'surfacearea_m2': sa,
                                                                  'vol_ML': vol,
                                                                  'catchuptotal_km2': ca,
                                                                  'group_name': demgroup,
                                                                  'wfill_MLperT': wfill,
                                                                  'bypass_MLperT': bypass})
                                
                            case _:
                                pass
                case _:
                    pass
                                            
    return params

# %%=====================================================================================================================
def read_scenario_oldtedi_v1(scenfile):
    pass


# %%=====================================================================================================================
# scenfile = r'C:/Users/robert.morden/OneDrive - Alluvium Consulting Australia/_Roberts stuff/Tools/STEDI/V1-2/Sample Data/test2.scn'
# params = read_scenario_file(scenfile)
fname = 'F8steadi_v1-24.scn'
params = read_scenario_file(fname)
