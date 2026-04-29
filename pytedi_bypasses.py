# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
January 2026

This is the code for setting up bypasses and other related functions.

Bypasses can either operate from:
    - a given start date to an end date, or
    - all year round.

Bypasses have a set flow capacity, eg 0.1 ML per day. That value can be determined by:
    - a value given in the original dam list, or
    - a catchment wide value (eg. 0.1 ML per day per sq.km.) which is then multiplied
      by the dam catchment to get a bypass capacity for a specific dam.
      
Other features which should appear here but have not been implemented include:
    - seepage through the dam wall and into the ground
    - flows returning to the dam (ie. re-use dams)
    - flows returning to the stream (ie. irrigation returns)
    THESE FEATURES WILL APPEAR IN FUTURE VERSIONS IF THERE IS A NEED FOR THEM.

@author: robert.morden
"""

import pandas as pd

# =====================================================================================================================
