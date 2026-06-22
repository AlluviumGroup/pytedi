# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
June 2026

The TEDI algorithm is based on the original paper by Nathan et al (2005), with several papers adding further to the data input methodology and calculation methods.

REFERENCES:
    Nathan, R., Jordan, P., Morden, R., 2005. Assessing the impact of farm dams on streamflows, Part I: Development of Simulation Tools. Australian Journal of Water … 9, 1–12. https://doi.org/10.1080/13241583.2005.11465259
    Nathan, R., Lowe, L., 2012. The hydrologic impacts of farm dams. Australasian Journal of Water Resources 16, 75–83. https://doi.org/10.7158/13241583.2012.11465405
    Fowler, K., Morden, R., Lowe, L., Nathan, R., 2015. Advances in assessing the impact of hillside farm dams on streamflow. Australian Journal of Water Resources 19. https://doi.org/10.1080/13241583.2015.1116182
    Morden, R., 2017. A new method of accounting for runoff dams, in: Syme, G., Hatton MacDonald, D., Fulton, B., Piantadosi, J. (Eds.), MODSIM2017, 22nd International Congress on Modelling and Simulation. Hobart, Australia, pp. 1676–1682. https://doi.org/10.36334/MODSIM.2017.L8.morden

@author: robert.morden
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime


logger = logging.getLogger(__name__)


from .scenario import read_scenario_file
from .damslist import process_STEDI_dams
from .bypasses import process_STEDI_bypasses
from .climate import process_STEDI_climate
from .demands import process_STEDI_demands
from .engine import calc_dams
from .data_io import write_results_global, write_results_individual, save_pytedi_model



# pytedi_version = '0.1' 
# pytedi_date = 'June 2026'
# pytedi_authors = 'Robert Morden and Ella Guthrie (Alluvium Consulting) and Joel Rahman (Flow Matters)'

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
        rundate               datetime                 date and time of last model run (nan if not run yet)
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
        catch_results         dataframe                Timeseries of water balance fluxes for the entire catchment
            sstore                float64                  Timeseries of start storage
            flow_up               float64                  Timeseries of upstream flow
            netevap               float64                  Timeseries of net evaporation (evap - rain)
            demd_sum              float64                  Timeseries of demand (unrestricted, the demand that would be extracted if water was available)
            bp                    float64                  Timeseries of bypassed flow aggregated over all dams, not just what comes out at the downstream end
            estore                float64                  Timeseries of end storage
            flow_down             float64                  Timeseries of downstream flow
            agg_impact            float64                  Timeseries of impact (upstream flow - downstream flow)
        indiv_results         dataframe                Timeseries of water balance fluxes for individual dams (only those marked by the 'output' flag in the damlist)
            istep                 float64                  Timestep number (starting from istep=0 at the start of the record) 
            idam                  float64                  Dam unique id
            date                  float64                  Date of result (should link exactly to istep) 
            sstore                float64                  Dam start storage 
            local_inflow          float64                  Dam local upstream inflows 
            updam_spill           float64                  Spills form all dams IMMEDIATELY upstream 
            netevap               float64                  Net evap for the dam (evap - rain) 
            demand                float64                  demand for the dam (unrestricted, the demand that would be extracted if water was available)
            bp                    float64                  Bypassed flow
            es                    float64                  Dam end storage 
            outflow               float64                  Dam outflow (excluding bypass, outflow represents dam spills only)
        '''
         
        self.title = 'Default title'
        self.timestep = 'day'
        self.calc_nat_or_obs = 'obs'
        self.cat_area_km2 = 1.0
        self.scale_limit = 0.8
        self.rundate = np.nan
        
        cols =  ['dam_id',          'ds_damid',     'surfacearea_m2',    'catchuptotal_km2', 'catchuplocal_km2',  'vol_ML',          
                 'year_start',      'group_name',    'demfactor',         'bypass_MLperT',   'bypass_start_ddmm', 
                 'bypass_end_ddmm', 'wfill_MLperT',  'wfill_start_ddmm',  'wfill_end_ddmm',  'output']
        
        types = ['int32',           'int32',         'float64',           'float64',         'float64',           'float64',         
                 'int32',           'string',        'float64',           'float64',         'int32', 
                 'int32',           'float64',       'int32',             'int32',           'int32']
        
        self.damlist = pd.DataFrame(columns=cols).astype(dict(zip(cols,types)))
        
        histindex = pd.DatetimeIndex(['1800-01-01', '2100-01-01'])
        histdata = [1.0,1.0]
        self.histoscale = pd.DataFrame(data=histdata, index=histindex, columns=['histoscale'])
        self.histoscale.index.name = 'Date'
        
        cols = ['rain', 'evap', 'flowup', 'flowdown']
        self.ts = pd.DataFrame(columns=cols,dtype='float32')

        cols = ['sstore', 'flow_up', 'netevap', 'demd_sum', 'bp', 'estore', 'flow_down', 'agg_impact']
        self.catch_results = pd.DataFrame(columns=cols,dtype='float32')

        cols =  ['istep', 'idam', 'sstore', 'local_inflow','updam_spill','netevap','demand', 'bp',     'es',     'outflow']
        types = ['int32', 'int32','float32','float32',     'float32',    'float32','float32','float32','float32','float32']   # first two columns are integers
        self.indiv_results = pd.DataFrame(columns=cols).astype(dict(zip(cols,types)))
        
    def run_model(self):
        global_results, alldam_results = calc_dams(self)
        self.catch_results = global_results
        self.indiv_results = alldam_results

        now = datetime.now()
        self.rundate = now.strftime('%Y-%m-%d %H:%M:%S')

        logger.info('Model run completed on %s', self.rundate)

    def save_results_global(self,outfile):
        write_results_global(self,outfile)
        logger.info('Global catchment water balance results saved to file: %s', outfile)

    def save_results_individual(self,outfile):
        write_results_individual(self,outfile)
        logger.info('Individual dam water balance results saved to file: %s', outfile)

    def save_model(self,fileprefix):
        save_pytedi_model(self,fileprefix)
        logger.info('Model files saved with prefix: %s', fileprefix)

    def open_model(self,fileprefix):
        logger.warning('open_model is not implemented yet (requested prefix: %s)', fileprefix)
        # model_dict = open_pytedi_model(fileprefix)
        # update model attributes

    def save_source_input(self,outfile):
        logger.warning('save_source_input is not implemented yet (requested file: %s)', outfile)
        
# %%=======================================================================================================================
def open_windows_STEDI_scenario(fname):
    
    stedi_params = read_scenario_file(fname)                                   # open the STEDI file and read the information     DONE
    
    dams = process_STEDI_dams(stedi_params)                                    # make sense of the dams                           DONE
    
    bpass,wfill = process_STEDI_bypasses(stedi_params,dams)                    # make sense of the bypasses                       DONE

    clim = process_STEDI_climate(stedi_params)                                 # make sense of the climate                        DONE
    
    d_ts, d_groups, d_factors = process_STEDI_demands(stedi_params,dams,clim)  # make sense of the demands                        DONE
    
    # define variable as a 'tedimodel' object
    model = tedimodel()
    
    # add basic information into the tedimodel object
    model.title = stedi_params['title']
    model.timestep = stedi_params['timestep']
    model.calc_nat_or_obs = stedi_params['calc_nat_or_obs']
    model.cat_area_km2 = stedi_params['cat_area_km2']
    
    # add dam list
    model.damlist['dam_id'] = dams.loc[:,'dam_id']
    model.damlist.loc[:,'ds_damid'] = dams.loc[:,'ds_damid']
    model.damlist.loc[:,'surfacearea_m2'] = dams.loc[:,'surfacearea_m2']
    model.damlist.loc[:,'vol_ML'] = dams.loc[:,'vol_ML']
    model.damlist.loc[:,'catchuptotal_km2'] = dams.loc[:,'catchuptotal_km2']
    model.damlist.loc[:,'catchuplocal_km2'] = dams.loc[:,'catchuplocal_km2']
    model.damlist.loc[:,'year_start'] = 0
    
    # add demand info to dam list
    model.damlist.loc[:,'group_name'] = d_groups
    model.damlist.loc[:,'demfactor'] = d_factors
    
    # add bypasses and winterfill to dam list
    model.damlist.loc[:,'bypass_MLperT'] = bpass.loc[:,'bypass_MLperT']
    model.damlist.loc[:,'bypass_start_ddmm'] = bpass.loc[:,'bypass_start_ddmm']
    model.damlist.loc[:,'bypass_end_ddmm'] = bpass.loc[:,'bypass_end_ddmm']

    model.damlist.loc[:,'wfill_MLperT'] = wfill.loc[:,'wfill_MLperT']
    model.damlist.loc[:,'wfill_start_ddmm'] = wfill.loc[:,'wfill_start_ddmm']
    model.damlist.loc[:,'wfill_end_ddmm'] = wfill.loc[:,'wfill_end_ddmm']
    
    # add climate and flow to ts
    model.ts['rain'] = clim['rain']
    model.ts['evap'] = clim['evap']
    if model.calc_nat_or_obs == 'nat':
        model.ts['flowdown'] = clim['flow']
    else:
        model.ts['flowup'] = clim['flow']
    
    # add demand timeseries to ts
    model.ts = model.ts.join(d_ts)
        
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
