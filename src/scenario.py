# -*- coding: utf-8 -*-
"""

pytedi - Python Tool for Estimating Dam Impacts
-----------------------------------------------

Dr Robert Morden
October 2025

These are the routines for converting old windows scenario files.
Users can:
    - convert multiple windows files to a individual python files. Input is:
        - a list of files with full path names and
        - a list (same length) of output files with full path names

    - convert multiple windows files to a combined python file. Input is:
        - a list of files with full path names and
        - a single output file with full path name
    
@author: robert.morden
"""

import pandas as pd
import numpy as np
from pathlib import Path

# =====================================================================================================================
def convert_winSTEDI_to_pyTEDI_singles(infiles,outfiles):
    pass

# =====================================================================================================================
def convert_winSTEDI_to_pyTEDI_multi(infiles,outfiles):
    pass

# =====================================================================================================================
def read_scenario_file(scenfile):
    
    # check what sort of scenario file it is
    scenfile_type = ''
    
    # read the second line
    # if the line is '# pyTEDI  Version 1.00' then we can proceed
    # if the line is 'STEDI  Version 1.00' then thats an old scenario. Give a warning.
    # if the line is anything else, file type not recognised. Give a warning.
    with open(scenfile) as stream:
        line1 = stream.readline()
        line2 = stream.readline()
        if line2 == 'STEDI  Version 1.00':
            scenfile_type = 'STEDI'
        else:
            scenfile_type = 'unknown'
            raise IOError(f"The input file is not a known TEDI or STEDI scenario format./n{scenfile}")
    
    if scenfile_type == 'STEDI':
        scenparams = read_scenario_winstedi_v1(scenfile)

    if scenfile_type == 'TEDI':
        scenparams = read_scenario_oldtedi_v1(scenfile)
    
    return scenparams

# =====================================================================================================================
def read_scenario_winstedi_v1(scenfile):
    pass

# =====================================================================================================================
def read_scenario_oldtedi_v1(scenfile):
    pass
