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
f1model,f1params = pytedi.open_windows_STEDI_scenario(fname)
f1model.run_model()
f1model.save_results_global(r'F1_pytedi_out_global.csv')
f1model.save_results_individual(r'F1_pytedi_out_indiv.csv')

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
