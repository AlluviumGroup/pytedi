import pandas as pd
import importlib
import pytedi
importlib.reload(pytedi)



fname = 'F8steadi_v1-24.scn'
newmodel, params = pytedi.open_windows_STEDI_scenario(fname)




#newmodel.run_model()
