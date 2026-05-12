# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
December 2025

This is the code for importing climate and inflows.
Climate can come from a csv, or a getdat file
Flow can come from a csv, or a getdat file

The logical process is:
    - gather required data (file names, field names, etc)
    - check if the input is a csv, getdat, or dataframe
    - call separate function for each type of input
    
@author: robert.morden
"""

import pandas as pd

