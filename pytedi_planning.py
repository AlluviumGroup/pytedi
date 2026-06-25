# -*- coding: utf-8 -*-
"""
Planning the code layout for pytedi
-----------------------------------------------

It should NOT be called 'pystedi', it sounds a bit like 'piss steady' which is a little bit wrong.

It needs to run with IDENTICAL RESULTS to windows STEDI

It should be able to read an existing STEDI scn file or batch file and convert it to a new format.

DAMS
- Distribution
- List of dams
- Surface areas by list or by formula
- catchment areas by lognormal distribution or stepwise linear equation
- Optional network list

DEMANDS
- Demand factor by formula, type, or list
- Demand pattern by climate, long term pattern, or 12 factors, then create long term pattern at the right timestep

CLIMATE AND INFLOW
- rain and evap by csv or getdat
- inflow by csv or getdat
- input from SILO??? No. Its too dicey to use directly.

BYPASSES AND SEEPAGE (AND RETURNS??)
- bypass info by list or by catchment area (big catchment = big bypass)
- seepage and returns not included yet

CALCULATIONS
- Calc natural or calc impacted
- surface area to volume equation
- flow factor???

SCENARIO FILE
- Not entirely sure how to do this.
- It needs to read the old scn file format.
- But what to do after that? What needs to be saved?? What format??

RUN
- When running, it should be able to produce the same global outputs as the windows version, but in a nicer format.
- Results for individual dams based on a user defined flag (one output file per dam giving the total water balance)
- Results only saved when the user calls something like 'save_results_global' or 'save_results_individual'

USER EXPERIENCE
- Should be run something like the following:
    
    import pytedi
    mymodel = pytedi.open_windows_STEDI_scenario(scn_file)              # open an old STEDI file and imort parameters
    mymodel.run()                                                       # run the model
    mymodel.save_results_global(outputfile1)                            # save catchment water balance data to a file
    mymodel.save_results_individual(outputfile2)                        # save catchment water balance data to a file
    mymodel.save_source_input(source_farmdam_input)                     # save an output file ready to use in eWater Source
    
- To achieve the above, there needs to be a package called 'pytedi' and a class called 'tedi_model'
- The class 'tedi_model' would need to store all input data including timeseries
- The class 'tedi_model' would need to have methods for running a model, and saving outputs
- The method for saving Source inputs should have options depending on how the Source model is set up (eg. all in one column, or split positives and negatives)
    
Additional functionality
------------------------
- Historical dam development:
    - The catchfile could define a year of construction.
    - The modelfile could define whether to use no scaling, historical scaling from the dam list, or global scaling based on a dictionary (eg. {1950:0.05, 1970:0.1, 2000:0.9, 2010:1.0})
    - Options would be 'None', 'list', or a dictionary

Package layout
--------------

pytedi/main           flow control and TEDI_model class
pytedi/scenario       read scenario file and assemble parameters into the class
pytedi/catchment      prepare basic information about the catchment
pytedi/dams           prepare a list of dams in a standard format
pytedi/demands        determine demand patterns and factors for each dam in the list
pytedi/climate        prepare the rainfall and evap in a standard format
pytedi/bypass         prepare bypass info (ond other features later such as seepage or flow returns)
pytedi/engine         the main engine which does the calculations for any given timestep (use NUMBA where possible)           # DONE
pytedi/outputs        write outputs to files (water balance and final list of dams and their parameters)

@author: robert.morden
"""
