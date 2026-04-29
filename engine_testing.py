# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 09:59:05 2026

@author: robert.morden
"""

import pandas as pd
import time
from pytedi_engine import calc_from_up_to_down 
from pytedi_engine import calc_from_down_to_up 

# Engine testing
# --------------

# import pandas as pd
# import numpy as np

# run_title = 'Test 1'
# timestep = 'month'
# calc_nat_or_obs = 'obs'
# cat_area = 13.24
# damlist_source = 'Test1_damlist.csv'
# clim_rainfile = 'Test1_clim.csv'
# clim_rainfield = 'Rain'
# clim_evapfile = 'Test1_clim.csv'
# clim_evapfield = 'Evap'
# clim_flowfile = 'Test1_clim.csv'
# clim_flowfield = 'Flow'

# demands_df = pd.read_csv('Test1_clim.csv',index_col=0,parse_dates=True,dayfirst=True)
# demands_df = pd.DataFrame(demands_df.iloc[:,0:2])

# rain_df = pd.read_csv(clim_rainfile,index_col=0,parse_dates=True,dayfirst=True)
# rain_df = pd.DataFrame(rain_df.loc[:,clim_rainfield])

# evap_df = pd.read_csv(clim_evapfile,index_col=0,parse_dates=True,dayfirst=True)
# evap_df = pd.DataFrame(evap_df.loc[:,clim_evapfield])

# flowin_df = pd.read_csv(clim_flowfile,index_col=0,parse_dates=True,dayfirst=True)
# flowin_df = pd.DataFrame(flowin_df.loc[:,clim_flowfield])

# histoscale_df = pd.read_csv(clim_flowfile,index_col=0,parse_dates=True,dayfirst=True)
# histoscale_df = pd.DataFrame(histoscale_df.loc[:,'History'])

# damlist_df = pd.read_csv(damlist_source)

# scale_limit = 0.8

# global_results, alldam_results = calc_from_up_to_down(damlist_df, demands_df, rain_df, evap_df, flowin_df, cat_area, scale_limit, histoscale_df)

# flowout_df = global_results['flow_down']
# global_results_up, alldam_results_up = calc_from_down_to_up(damlist_df, demands_df, rain_df, evap_df, flowout_df, cat_area, scale_limit, histoscale_df)

# flowin_calc = global_results_up['flow_up']

# flowin_compare = pd.DataFrame({'orig flow in':flowin_df.iloc[:,0],'calc flow in':flowin_calc})
# flowin_compare.plot()

'''
Where am I up to?

The downstream flow calculations seem to run fully.
Have compared a simple model with Excel - results match to 12 decimal places.
The downstream calcs are working perfectly.
The upstream calcs return the original flow.

ALL GOOD!!

Still need to check historical scaling and a few other features like that.

'''

import matplotlib.pyplot as plt

run_title = 'Test 3'
timestep = 'day'
calc_nat_or_obs = 'obs'
cat_area = 3900
damlist_source = 'Test3_damlist.csv'
clim_rainfile = 'Test3_clim.csv'
clim_rainfield = 'Rain'
clim_evapfile = 'Test3_clim.csv'
clim_evapfield = 'Evap'
clim_flowfile = 'Test3_clim.csv'
clim_flowfield = 'Flow'

startdate = '1967-01-01' 
enddate = '2025-12-31'

demands_df = pd.read_csv('Test3_clim.csv',index_col=0,parse_dates=True,dayfirst=True)
demands_df = pd.DataFrame(demands_df.iloc[:,0:2])
demands_df = demands_df.loc[startdate:enddate,:]

rain_df = pd.read_csv(clim_rainfile,index_col=0,parse_dates=True,dayfirst=True)
rain_df = pd.DataFrame(rain_df.loc[startdate:enddate,clim_rainfield])

evap_df = pd.read_csv(clim_evapfile,index_col=0,parse_dates=True,dayfirst=True)
evap_df = pd.DataFrame(evap_df.loc[startdate:enddate,clim_evapfield])

flowin_df = pd.read_csv(clim_flowfile,index_col=0,parse_dates=True,dayfirst=True)
flowin_df = pd.DataFrame(flowin_df.loc[startdate:enddate,clim_flowfield])

histoscale_df = pd.read_csv(clim_flowfile,index_col=0,parse_dates=True,dayfirst=True)
histoscale_df = pd.DataFrame(histoscale_df.loc[startdate:enddate,'History'])

damlist_df = pd.read_csv(damlist_source)

scale_limit = 0.8

t1 = time.time()
global_results, alldam_results = calc_from_up_to_down(damlist_df, demands_df, rain_df, evap_df, flowin_df, cat_area, scale_limit, histoscale_df)
t2 = time.time()
flowout_df = global_results['flow_down']
global_results_up, alldam_results_up = calc_from_down_to_up(damlist_df, demands_df, rain_df, evap_df, flowout_df, cat_area, scale_limit, histoscale_df)
t3 = time.time()
flowin_calc = global_results_up['flow_up']

flowin_compare = pd.DataFrame({'orig flow in':flowin_df.iloc[:,0],'calc flow in':flowin_calc})
plt.figure()
flowin_compare.plot()
plt.figure()
flowin_compare.plot.scatter(x='orig flow in',y='calc flow in',loglog=True);

flowin_compare['diff'] = flowin_compare['orig flow in'] - flowin_compare['calc flow in']
plt.figure()
flowin_compare['diff'].plot.hist(bins=20)

dates_df = flowin_df.index.to_frame(name='Date').reset_index(drop=True)
alldam_results = alldam_results.merge(dates_df,left_on='istep',right_index=True,how='left')
print('Downstream processing time = ' + str(t2-t1))
print('Upstream processing time = ' + str(t3-t2))

'''
10 dams

Processing times (normal python)
Downstream processing time = 2.521136999130249
Upstream processing time = 7.852887153625488

Processing times (NUMBA applied to singlestep function only)
Downstream processing time = 0.9440851211547852
Upstream processing time = 1.0841097831726074

5000 dams

Processing times (normal python)
Downstream processing time = 901.6892182826996 (15 minutes)
Upstream processing time = 8040.518349409103 (134 minutes)

Processing times (NUMBA applied to singlestep function only)
Downstream processing time = 7.2231621742248535
Upstream processing time = 70.03484153747559 (1 minute)

Processing times (NUMBA applied to all 3 functions)
Downstream processing time = 8.116048574447632
Upstream processing time = 67.07137179374695

Holy schmoly. That's fast.
'''
