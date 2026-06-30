import pandas as pd
import numpy as np
import importlib
import pytedi
importlib.reload(pytedi)



fname = 'F8steadi_v1-24.scn'
newmodel, params = pytedi.open_windows_STEDI_scenario(fname)
newmodel.run_model()

newmodel.save_results_global('test1_catchment_results.csv')
newmodel.save_results_individual('test1_individualdam_results.csv')
newmodel.save_model('test1_model')

fname = 'Current_new.scn'
cbup, cbup_params = pytedi.open_windows_STEDI_scenario(fname)
cbup.run_model()

cbup.save_results_global('cbup_catchment_results.csv')
cbup.save_results_individual('cbup_individualdam_results.csv')
cbup.save_model('cbup_model')

fname = r'C:\Users\robert.morden\OneDrive - Alluvium Consulting Australia\_Roberts stuff\Tools\Python\pytedi\pytedi_github\10days.scn'
model_10days,params = pytedi.open_windows_STEDI_scenario(fname)

model_10days.damlist.loc[1,'output'] = 1

# x = model_10days.damlist.loc[:,'catchuplocal_km2']
# model_10days.damlist.loc[:,'catchuplocal_km2'] = np.trunc(x*100)/100
model_10days.run_model()
model_10days.save_results_global(r'C:\Users\robert.morden\OneDrive - Alluvium Consulting Australia\_Roberts stuff\Tools\Python\pytedi\pytedi_github\Out1_pytedi_10days.csv')
model_10days.save_results_individual(r'C:\Users\robert.morden\OneDrive - Alluvium Consulting Australia\_Roberts stuff\Tools\Python\pytedi\pytedi_github\Out2_pytedi_10days.csv')

fname = 'F1.scn'
f1model = pytedi.open_windows_STEDI_scenario(fname)
dam_number = 27                                                     # this is the 27th dam in the “damlist”
f1model.damlist.loc[dam_number,'output'] = 1                        # set the flag to 1 to produce results
f1model.run_model()
f1model.save_results_global(r'F1_pytedi_out_global.csv')
f1model.save_results_individual(r'F1_pytedi_out_indiv.csv')
f1model.save_model('F1_model')

fname = 'F4_damlist.scn'
f4model,f4params = pytedi.open_windows_STEDI_scenario(fname)
f4model.run_model()
f4model.save_results_global(r'F4_pytedi_out_global.csv')
f4model.save_results_individual(r'F4_pytedi_out_indiv.csv')
f4model.save_model('F4_pytedi_model')

fname = 'Test1_5dams.scn'
t1model,t1params = pytedi.open_windows_STEDI_scenario(fname)
t1model.run_model()
t1model.save_model("test1_5dams_pytedi")
t1model.save_results_global('test1_5dams_pytedi_globalout.csv')

fname = 'Test2_5dams_pytedi_params.scn'
t2model = pytedi.open_pytedi_scenario(fname)
t2model.run_model()
t2model.save_model("test2_5dams_pytedi")
t2model.save_results_global('test2_5dams_pytedi_globalout.csv')

parameter_file = ('F1_model_params.scn')
mymodel2 = pytedi.open_pytedi_scenario(parameter_file)       # opens the model and assigns it to ‘mymodel2’

# set up some alternative scaling dates and values
histdates = ['1950-01-01', '2000-01-01', '2010-01-01', '2030-01-01']
histvalues = [0.0, 0.0, 1.0, 1.0]                                          # 0% in 1950, 40% in 2000, 100% in 2010 onwards

# add them to the model and run
mymodel2.histoscale = mymodel2.histoscale.reindex(pd.DatetimeIndex(histdates))
mymodel2.histoscale.loc[:,'histoscale'] = histvalues
mymodel2.run_model()                                                     # now run the model
# plot the impact so the long term trend is visible
mymodel2.catch_results['agg_impact'].resample('YS').sum().plot()
