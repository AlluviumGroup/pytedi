# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
December 2025

This is the code for setting up demand information.
Demands are composed of:
    - a demand factor (proportion of dam that is needed for on-site usage each year), and
    - a demand pattern (proportion of demand that should be applied at each timestep)
    - the pattern is multiplied by the factor
    
Demand factors can be sourced from:
    - the dam list (if the user has provided the field 'dem factor') giving a unique demand factor per dam
    - the demand group (ie. stock and domestic might have a dem factor of 0.5)

Demand patterns can be sourced from:
    - climate data ('smoothed net evap' as used in PRIDE = PET - rainfall, convert to 2 week moving average, then remove negatives)
    - long term pattern from an external file (may need to correct the timestep)
    - a repeating pattern of 12 monthly values
    - patterns are different for each demand group
    
Demand groups are specified:
    - in the dam list (with each dam assigned to a group by the user in the input data)
    - by stepwise linear relationship with volume (eg. vol<5ML are domestic, vol>5ML are irrigation)

Logical sequence of calculations:
    - determine demand group method ('volume', 'list') (def assign_dem_groups)
    - assign each dam to a demand group
    - save info as a field in the dam list
    
    - determine demand factor method ('group', 'list') (def assign_dem_factors)
    - assign demand factors to each dam
    - save info as a field in the dam list
   
    - determine demand pattern method ('netevap', 'pattern', '12months') (def create_dem_patterns)
    - for each demand group
    - if 'climate'
        - read PET file
        - calc net evap
        - convert to pattern with mean ann sum = 1
    - if 'pattern'
        - read pattern file
        - convert to pattern with mean ann sum = 1
    - if '12months'
        - read 12 values
        - convert to pattern with mean ann sum = 1
    - save info in a separate 'dem_patterns' dataframe with columns = demand group names
        
All patterns are converted to a long term sequence ov values at the correct timestep with the mean annual sum = 1.0.       <<<<< SHOULD I DO THIS?? OR TRUST THE USER INPUT???
All patterns are then multiplied by the demand factor LATER during run time.

@author: robert.morden
"""

import pandas as pd
