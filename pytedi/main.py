# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
October 2025

The TEDI algorithm is based on the original paper by Nathan et al (2005), with several papers adding further to the data input methodology and calculation methods.

REFERENCES:
    Nathan, R., Jordan, P., Morden, R., 2005. Assessing the impact of farm dams on streamflows, Part I: Development of Simulation Tools. Australian Journal of Water … 9, 1–12. https://doi.org/10.1080/13241583.2005.11465259
    Nathan, R., Lowe, L., 2012. The hydrologic impacts of farm dams. Australasian Journal of Water Resources 16, 75–83. https://doi.org/10.7158/13241583.2012.11465405
    Fowler, K., Morden, R., Lowe, L., Nathan, R., 2015. Advances in assessing the impact of hillside farm dams on streamflow. Australian Journal of Water Resources 19. https://doi.org/10.1080/13241583.2015.1116182
    Morden, R., 2017. A new method of accounting for runoff dams, in: Syme, G., Hatton MacDonald, D., Fulton, B., Piantadosi, J. (Eds.), MODSIM2017, 22nd International Congress on Modelling and Simulation. Hobart, Australia, pp. 1676–1682. https://doi.org/10.36334/MODSIM.2017.L8.morden

@author: robert.morden
"""

import pandas as pd

from .scenario import read_scenario_file
from .damslist import process_STEDI_dams
from .bypasses import process_STEDI_bypasses
from .climate import process_STEDI_climate
from .demands import process_STEDI_demands
from .engine import calc_dams

# %%=======================================================================================================================
class tedimodel():

    # initialise
    def __init__(self):
        
        '''
        Key variables for the tedimodel class
        -------------------------------------
        
        Variable              Type (values)            Description
        
        title                 string                   Name of model run (eg. Avoca River historic 1975-2026)
        timestep              string ('day'/'month')   Timestep for climate, flow, and demands
        calc_nat_or_obs       string ('nat'/'obs')     Direction of calculation (calculate upstream natural, or downstream observed)
        cat_area_km2          float64                  Total catchment area in km2
        scale_limit           float64                  If local areas for each dam sum to more than cat_area_km2 x scale limit, the areas will be proprtionally reduced.
        damlist               dataframe                List of dams in the catchment and their characteristics
            dam_id                integer                  dam unique id
            ds_dam_id             integer                  unique id of the dam downstream (-99 if none downstream)
            surfacearea_m2        float64                  dam surface area (m2)
            catchuptotal_km2      float64                  total catchment area upstream (including other dams)
            catchuplocal_km2      float64                  local catchment area upstream (excluding other dams)
            vol_ML                float64                  maximum capacity (ML)
            year_start            integer                  year when dam is completed
            group_name            string                   name of demand group (eg. stock and domestic, irrigaton, vineyard, etc)
            demfactor             float64                  mean annual demand as a proportion of dam capacity
            bypass_MLperT         float64                  bypass flow rate in ML per day/month
            bypass_start_ddmm     integer                  start date of bypass (eg. 1 Jan = 0101, 15th July = 1507)
            bypass_end_ddmm       integer                  end date of bypass (eg. 1 Jan = 0101, 15th July = 1507)
            wfill_MLperT          float64                  bypass flow rate in ML per day/month
            wfill_start_ddmm      integer                  start date of bypass (eg. 1 Jan = 0101, 15th July = 1507)
            wfill_end_ddmm        integer                  end date of bypass (eg. 1 Jan = 0101, 15th July = 1507)
            output                integer                  flag = 1 to produce water balance results for this dam, or 0 otherwise
        histoscale            dataframe                Timeseries of historic scaling factors to apply (eg. 01/01/1950 = 0.0, 1/1/2010 = 1.0, 1/1/2050 = 1.0)
        ts                    dataframe                Timeseries of demand, climate, and flow
            demands               float64                  Timeseries of demand patterns, 1 column per demand type
            rain                  float64                  Timeseries of rain (mm), 1 column 'rain'
            evap                  float64                  Timeseries of evap (mm), 1 column 'evap'
            flowup                float64                  Timeseries of flow upstream of dams (ie. no impact) (mm), 1 column 'flowup'
            flowdown              float64                  Timeseries of flow downstream of dams (ie. no impact) (mm), 1 column 'flowdown'
        '''
         
        
        self.title = 'Default title'
        self.timestep = 'day'
        self.calc_nat_or_obs = 'obs'
        self.cat_area_km2 = 1.0
        self.scale_limit = 0.8
        
        damlistcols = ['dam_id',          'ds_dam_id',     'surfacearea_m2',    'catcharea_km2',   'vol_ML',          
                       'year_start',      'group_name',    'demfactor',         'bypass_MLperT',   'bypass_start_ddmm', 
                       'bypass_end_ddmm', 'wfill_MLperT',  'wfill_start_ddmm',  'wfill_end_ddmm', 'output']
        
        self.damlist = pd.DataFrame(columns=damlistcols)
        
        histindex = pd.DatetimeIndex(['1800-01-01', '2100-12-31'])
        histdata = [1.0,1.0]
        self.histoscale = pd.DataFrame(data=histdata, index=histindex, columns=['histoscale'])
        
        tscols = ['rain', 'evap', 'flowup', 'flowdown']
        self.ts = pd.DataFrame(columns=tscols,dtype='float32')
                
    def run_model(self):
        print('Let\'s pretend the model just ran. Process, process, kaboom. We are done.')
    
    def save_results_global(self,outfile):
        print(f'Let\'s pretend the global results just saved to the file {outfile}.')
    
    def save_results_individual(self,outfileprefix):
        print(f'Let\'s pretend the individual dam results just saved to the file {outfileprefix}.')
    
    def save_model(self,outfile):
        print(f'Let\'s pretend the model parameters just saved to the file {outfile}.')

    def save_source_input(self,outfile):
        print(f'Let\'s pretend a SOURCE input file was just saved to the file {outfile}.')

# %%=======================================================================================================================
def open_windows_STEDI_scenario(fname):
    
    stedi_params = read_scenario_file(fname)                                   # open the STEDI file and read the information     DONE
    
    dams = process_STEDI_dams(stedi_params)                                    # make sense of the dams                           DONE
    
    bpass,wfill = process_STEDI_bypasses(stedi_params,dams)                    # make sense of the bypasses                       DONE

    clim = process_STEDI_climate(stedi_params)                                 # make sense of the climate                        DONE
    
    dem_ts,dem_f = process_STEDI_demands(stedi_params,dams,clim)               # make sense of the demands                        DONE
    
    # define variable as a 'tedimodel' object
    model = tedimodel()
    
    # add basic information into the tedimodel object
    model.title = stedi_params['title']
    model.timestep = stedi_params['timestep']
    model.calc_nat_or_obs = stedi_params['calc_nat_or_obs']
    model.cat_area_km2 = stedi_params['cat_area_km2']
    
    # add dam list
    model.damlist = dams                            # <<<<<< THIS NEEDS MORE WORK - WHAT IF THE SCENARIO FILE INCLUDES A LIST OF DAMS??? WILL COLUMNS BE CORRECT??
    
    # add demand factors to dam list              # <<<<<< THIS NEEDS MORE WORK
    
    # add bypasses and winterfill to dam list     # <<<<<< THIS NEEDS MORE WORK
    
    # add climate and flow to ts
    model.ts['rain'] = clim['rain']
    model.ts['evap'] = clim['evap']
    if model.calc_nat_or_obs == 'nat':
        model.ts['flowdown'] = clim['flow']
    else:
        model.ts['flowup'] = clim['flow']
    
    # add demand timeseries to ts
    model.ts = model.ts.join(dem_ts)
    
    # add demand factors to damlist
    #mod.damlist['demfactor'] = dem_f             # <<<<<< THIS NEEDS MORE WORK
    
    return model, stedi_params          # can comment out the stedi_params when testing is complete

# %%=======================================================================================================================
def open_pytedi_scenario(prefix):
    
    # open json or yaml file
    
    # open timeseries file
    
    # open dam list file
    
    # assign data in file to a tedimodel object
    model = tedimodel()
    
    # return the model
    return model

# %%=======================================================================================================================
def save_pytedi_scenario(prefix):
    
    # write json or yaml file
    
    # write timeseries file
    
    # write dam list file
    
    return
