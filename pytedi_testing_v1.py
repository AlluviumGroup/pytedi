import pandas as pd
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

