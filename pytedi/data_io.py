"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
June 2026

These are the functions for reading and writing model data in a native pytedi format.
Reading the old STEDI files needed over 1000 lines of code. Hopefully the native format will be quicker and easier.
    
@author: robert.morden
"""

import pandas as pd
import numpy as np
import os
import yaml
import io
from . import config

# %%=======================================================================================================================
def write_results_global(model,outfile):
    
    out_cols =  ['sstore', 'flow_up', 'netevap', 'demd_sum', 'estore', 'flow_down','bp','agg_impact']    # swapped column position of bypass flow
    out_df = model.catch_results[out_cols].copy()

    nice_cols = ['Start storage (ML)','Upstream flow (ML)','Net evap (ML)','Unrestricted demand (ML)','End Storage (ML)','Downstream flow (ML)','Bypassed flow (ML)','Total impact (ML)']
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

    out_cols =  ['idam', 'date', 'sstore', 'local_inflow', 'updam_spill', 'netevap', 'demand', 'es', 'outflow','bp']    # swapped column position of bypass flow, remove istep
    out_df = model.indiv_results[out_cols].copy()

    nice_cols = ['Dam ID','Date of obs','Start storage (ML)','Local upstream runoff (ML)','Upstream spills (ML)','Net evap (ML)','Unrestricted demand (ML)','End storage (ML)', 'Downstream spills (ML)', 'Bypassed flow (ML)']
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
        
    class CsvString(str):
        pass 
    def csv_string_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    
    # Define a custom representer to force plain style (no quotes)
    def plain_string_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='')

    # Register the representer for all Python string types
    yaml.SafeDumper.add_representer(str, plain_string_representer)
    
    histoscale_csv = io.StringIO()
    model.histoscale.to_csv(histoscale_csv,index=True)
    yaml.add_representer(CsvString, csv_string_representer)


    histoscale_string = model.histoscale.to_csv(lineterminator='\n')
    
    # save model parameter file
    model_data = {
        'Model title': model.title,
        'Model timestep': model.timestep,
        'Calculating natural or observed?': model.calc_nat_or_obs,
        'Total catchment area (km2)': model.cat_area_km2,
        'Scale limit': model.scale_limit,
        'Date of last model run': model.rundate,
        'File containing list of dams': dam_file,
        'File containing climate and demands': ts_file,
        'Historical scaling factors (linear adjustment of impacts after processing) (date, factor)': histoscale_string
    }
    
    def literal_string_representer(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
        # return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    yaml.SafeDumper.add_representer(str, literal_string_representer)

    with open(param_file, 'w') as f:
        f.write("# pytedi - Python tool for estimating dam impacts\n")
        f.write('# ===============================================\n')
        f.write(f"# Version {toolvers} - {tooldate}\n")
        f.write(f'# Authors - {toolauth}\n')
        f.write('# -----------------------\n')
        f.write('# MODEL FILE - PARAMETERS\n')
        f.write('# -----------------------\n')
        yaml.dump(model_data, f, sort_keys=False, default_flow_style=False, Dumper=yaml.SafeDumper)
    
    # save damlist
    with open(dam_file, 'w') as f:
        f.write("# pytedi - Python tool for estimating dam impacts\n")
        f.write('# ===============================================\n')
        f.write(f"# Version {toolvers} - {tooldate}\n")
        f.write(f'# Authors - {toolauth}\n')
        f.write(f'# File containing parameters - {param_file}\n')
        f.write(f'# File containing climate and demands - {ts_file}\n')
        f.write('# -------------------------\n')
        f.write('# MODEL FILE - LIST OF DAMS\n')
        f.write('# -------------------------\n')
        model.damlist.to_csv(f, lineterminator='\n')
        
    # save timeseries
    with open(ts_file, 'w') as f:
        f.write("# pytedi - Python tool for estimating dam impacts\n")
        f.write('# ===============================================\n')
        f.write(f"# Version {toolvers} - {tooldate}\n")
        f.write(f'# Authors - {toolauth}\n')
        f.write(f'# File containing parameters - {param_file}\n')
        f.write(f'# File containing list of dams - {dam_file}\n')
        f.write('# ----------------------------------------------\n')
        f.write('# MODEL FILE - TIMESERIES OF CLIMATE AND DEMANDS\n')
        f.write('# ----------------------------------------------\n')
        model.ts.to_csv(f, lineterminator='\n')

    # save histoscale
     
# %%=======================================================================================================================
def add_suffix_to_filename(filename, suffix, extension):
    base, ext = os.path.splitext(filename)
    if not ext:  # If there is no extension, use '.scn'
        ext = extension
    return f"{base}_{suffix}.{ext}"

#%%========================================================================================================================
def open_pytedi_model(outfile):
    pass
