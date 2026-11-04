"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
November 2026

These are the functions for reading and writing model data in a native pytedi format.
Reading the old STEDI files needed over 1000 lines of code. Hopefully the native format will be quicker and easier.
    
@author: robert.morden
"""

import pandas as pd
import numpy as np
import os
import io
from . import config

import tomllib
#import tomli_w


# %%=======================================================================================================================
def write_results_global(model,outfile):
    
    #out_cols =  ['sstore', 'flow_up', 'netevap', 'demd_sum', 'estore', 'flow_down','bp','agg_impact']    # swapped column position of bypass flow
    out_cols = ['sstore', 'flow_up', 'netevap', 'netevap_actual', 'demand', 'demand_actual', 'wf', 'wf_actual', 'bp', 'bp_actual', 'estore', 'spills', 'flow_down', 'agg_impact']
    out_df = model.catch_results[out_cols].copy()

    nice_cols = ['Start storage (ML)','Upstream flow (ML)','Net evap (Pot) (ML)','Net evap (Act) (ML)','Demand (Pot) (ML)','Demand (Act) (ML)',
                 'WFill (Pot) (ML)', 'WFill (Act) (ML)', 'Bypass (Pot) (ML)', 'Bypass (Act) (ML)',
                 'End Storage (ML)','Spills (ML)','Downstream flow (ML)','Total impact (ML)']
    out_df.columns = nice_cols
    
    if model.timestep == 'day':
        stepstring = 'daily timestep'
    elif model.timestep == 'month':
        stepstring = 'monthly timestep'
    
    if model.calc_nat_or_obs == 'nat':
        calcstring = 'calculating natural (upstream) given observed (downstream)'
    elif model.calc_nat_or_obs == 'obs':
        calcstring = 'calculating observed (downstream) given natural (upstream)'

    with open(outfile, mode="w", encoding="utf-8") as f:
        f.write('# pytedi - Python tool for estimating dam impacts\n')
        f.write('# ===============================================\n')
        f.write(f'# Run title - {model.title}\n')
        f.write(f'# Run timestep/direction - {stepstring}, {calcstring}\n')
        f.write(f'# Run date - {model.rundate}\n')
        f.write('# --------------------------------------------\n')
        f.write('# OUTPUT FILE - GLOBAL CATCHMENT WATER BALANCE\n')
        f.write('# --------------------------------------------\n')
        out_df.to_csv(f,lineterminator='\n')
        
    
        
# %%=======================================================================================================================
def write_results_individual(model,outfile):

    #out_cols =  ['idam', 'date', 'sstore', 'local_inflow', 'updam_spill', 'netevap', 'demand', 'es', 'outflow','bp']    # swapped column position of bypass flow, remove istep
    out_cols = ['dam_id', 'date', 'sstore', 'local_inflow','updam_spill','netevap','netevap_actual','demand', 'demand_actual','wf','wf_actual','bp','bp_actual','es','spills', 'outflow']
    out_df = model.indiv_results[out_cols].copy()

    nice_cols = ['Dam ID','Date of obs','Start storage (ML)','Local upstream runoff (ML)','Upstream spills (ML)',
                 'Net evap (Pot) (ML)','Net evap (Act) (ML)','Demand (Pot) (ML)','Demand (Act) (ML)',
                 'WFill (Pot) (ML)', 'WFill (Act) (ML)', 'Bypass (Pot) (ML)', 'Bypass (Act) (ML)',
                 'End storage (ML)', 'Downstream spills (ML)', 'Downstream flow (ML)']
    out_df.columns = nice_cols
    
    if model.timestep == 'day':
        stepstring = 'daily timestep'
    elif model.timestep == 'month':
        stepstring = 'monthly timestep'
    
    if model.calc_nat_or_obs == 'nat':
        calcstring = 'calculating natural (upstream) given observed (downstream)'
    elif model.calc_nat_or_obs == 'obs':
        calcstring = 'calculating observed (downstream) given natural (upstream)'

    with open(outfile, mode="w", encoding="utf-8") as f:
        f.write('# pytedi - Python tool for estimating dam impacts\n')
        f.write('# ===============================================\n')
        f.write(f'# Run title - {model.title}\n')
        f.write(f'# Run timestep/direction - {stepstring}, {calcstring}\n')
        f.write(f'# Run date - {model.rundate}\n')
        f.write('# -------------------------------------------\n')
        f.write('# OUTPUT FILE - INDIVIDUAL DAMS WATER BALANCE\n')
        f.write('# -------------------------------------------\n')
        out_df.to_csv(f,lineterminator='\n')
        
    
        
# %%=======================================================================================================================
def save_pytedi_model(model,outfile):

    param_file = add_suffix_to_filename(outfile,'params','scn')
    dam_file = add_suffix_to_filename(outfile,'dams','csv')
    ts_file = add_suffix_to_filename(outfile,'timeseries','csv')
    toolvers = config.pytedi_version
    tooldate = config.pytedi_date
    toolauth = config.pytedi_authors
    
    histdates = model.histoscale.index.strftime("%Y-%m-%d")
    joindates = ", ".join(f'"{d}"' for d in histdates)
    histfactors = model.histoscale['histoscale'].to_list()
    joinfactors = ", ".join(str(f) for f in histfactors)

    vary_surfarea_toml = str(bool(model.vary_surfarea)).lower()                 # TOML booleans are lowercase true/false

    toml_str = f"""# pytedi - Python tool for estimating dam impacts
# ===============================================
#
# Version {toolvers} - {tooldate}
# Authors - {toolauth}
#
# -----------------------
# MODEL FILE - PARAMETERS
# -----------------------
#

model_title =                     "{model.title}"

model_timestep =                  "{model.timestep}"

calculating_natural_or_observed = "{model.calc_nat_or_obs}"

total_catchment_area =            {model.cat_area_km2}

scale_limit =                     {model.scale_limit}

variable_surface_areas =          {vary_surfarea_toml}

volume_to_surfarea_a =            {model.vol_surfarea_a}
volume_to_surfarea_b =            {model.vol_surfarea_b}

starting_storage_proportion =     {model.startstore_propfull}

date_last_run =                   "{model.rundate}"

damlist_file =                    '{dam_file}'

timeseries_file =                 '{ts_file}'

historical_scaling_dates   =      [{joindates}]
historical_scaling_factors =      [{joinfactors}]
"""
    
    # Write the TOML file
    with open(param_file, "w") as f:
        f.write(toml_str)
    
    head_str = f"""# pytedi - Python tool for estimating dam impacts
# ===============================================
#
# Version {toolvers} - {tooldate}
# Authors - {toolauth}
#
# -------------------------
# MODEL FILE - LIST OF DAMS
# -------------------------
# Model title =                          {model.title}
# File containing parameters =           {param_file}
# File containing climate and demands =  {ts_file}
# -------------------------
#
# dam_id            = unique id for each dam (catchment outlet not included in the list))
# ds_damid          = unique id for the next downstream dam
# surfacearea_m2    = dam surface area (m2)
# catchuptotal_km2  = dam total upstream area including area impounded by upstream dams (km2)
# catchuplocal_km2  = dam local upstream area excluding area impounded by upstream dams (km2)
# vol_ML            = dam maxium capacity (ML)
# year_start        = year the dam was commissioned (can be set to 0 if historical scaling is not needed)
# group_name        = the name of the demand group, such as 'irrigation' or 'stock and domestic'
# demfactor         = the average annual demand expressed as a proportion of the dam capacity
# bypass_MLperT     = the flow rate of the bypass (ML per timestep)
# bypass_start_mmdd = the start of the bypass season as integer mmdd eg. 1st March would be 0301, or 15th June would be 0615
# bypass_end_mmdd   = the end of the bypass season as integer mmdd eg. 1st March would be 0301, or 15th June would be 0615
# wfill_MLperT      = the flow rate of winterfill pumping (ML per timestep)
# wfill_start_mmdd  = the start of the winterfill season as integer mmdd eg. 1st March would be 0301, or 15th June would be 0615
# wfill_end_mmdd    = the end of the winterfill season as integer mmdd eg. 1st March would be 0301, or 15th June would be 0615
# output            = set to 1 to flag that results for this individual dam should be reported in the individual results file (any other value will give no results output)
# demand_id         = integer linked to the group_name
#
"""
    
    # Write the file
    with open(dam_file, "w") as f:
        f.write(_strip_line_indents(head_str))                                 # '#' must be at column 0 so pandas comment='#' skips it
        model.damlist.to_csv(f, lineterminator='\n')
        
    head_str = f"""# pytedi - Python tool for estimating dam impacts
# ===============================================
#
# Version {toolvers} - {tooldate}
# Authors - {toolauth}
#
# ----------------------------------------------
# MODEL FILE - TIMESERIES OF CLIMATE AND DEMANDS
# ----------------------------------------------
# Model title =                   {model.title}
# File containing parameters =    {param_file}
# File containing list of dams =  {dam_file}
# ----------------------------------------------
#
# rain               = rainfall (mm)
# evap               = evaporation from the surface of a dam (mm)
# flowup             = flow upstream of farm dams (also known as 'natural' or 'unimpacted' or 'no dams' flow) (ML)
# flowdown           = flow downstream of farm dams (also known as 'impacted' or 'with dams' flow) (ML)
# remaining columns  = demand timeseries for different types of dams (unitless - multiplied by demand factor to represent a proportion of the dam volume extracted each day)
#
"""
    
    # Write the file
    with open(ts_file, "w") as f:
        f.write(_strip_line_indents(head_str))                                 # '#' must be at column 0 so pandas comment='#' skips it
        model.ts.to_csv(f, lineterminator='\n')
    

# %%=======================================================================================================================
def add_suffix_to_filename(filename, suffix, extension):
    base, ext = os.path.splitext(filename)
    if not ext:  # If there is no extension, use '.scn'
        ext = extension
    return f"{base}_{suffix}.{extension}"

# %%=======================================================================================================================
def _strip_line_indents(text):
    '''Remove leading whitespace from every line so that '#' comment markers sit
    at column 0. Header blocks are built from indented triple-quoted f-strings;
    without this, pandas read_csv(comment='#') fails to skip the header.'''
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(line.lstrip() for line in text.splitlines()) + trailing

#%%========================================================================================================================
def open_pytedi_model(outfile):
    
    # open the parameters file (tomllib requires a binary stream)
    with open(outfile,"rb") as f:
        toml_data_read = tomllib.load(f)

    pyparams = {}
    
    pyparams['model_title'] = toml_data_read["model_title"]
    pyparams['model_timestep'] = toml_data_read["model_timestep"]
    pyparams['calc_nat_or_obs'] = toml_data_read["calculating_natural_or_observed"]
    pyparams['cat_area_km2'] = toml_data_read["total_catchment_area"]
    pyparams['scale_limit'] = toml_data_read["scale_limit"]
    pyparams['vary_surfarea'] = toml_data_read["variable_surface_areas"]
    pyparams['vol_surfarea_a'] = toml_data_read["volume_to_surfarea_a"]
    pyparams['vol_surfarea_b'] = toml_data_read["volume_to_surfarea_b"]
    pyparams['startstore_propfull'] = toml_data_read["starting_storage_proportion"]
    pyparams['rundate'] = toml_data_read["date_last_run"]
    pyparams['dam_file'] = toml_data_read["damlist_file"]
    pyparams['ts_file'] = toml_data_read["timeseries_file"]

    histodates = toml_data_read["historical_scaling_dates"]
    histofactors = toml_data_read["historical_scaling_factors"]
    
    histoscale = pd.DataFrame({'histoscale': np.asarray(histofactors, dtype='float64')},
                              index=pd.DatetimeIndex(pd.to_datetime(histodates)))
    histoscale.index.name = 'Date'
    pyparams['histoscale'] = histoscale
    
    # open the dam list file (skip the leading '#' comment header). Only group_name
    # is pinned; integer-like columns (e.g. 'output', 'year_start') may legitimately
    # contain NaN, so let pandas infer numeric dtypes rather than forcing int.
    pyparams['damlist'] = pd.read_csv(pyparams['dam_file'], index_col=0, comment='#',
                                      dtype={'group_name': 'string'})

    # open the timeseries file (skip the leading '#' comment header)
    pyparams['ts'] = pd.read_csv(pyparams['ts_file'], index_col=0, comment='#',
                                 parse_dates=[0], dtype=np.float64)
    
    return pyparams
