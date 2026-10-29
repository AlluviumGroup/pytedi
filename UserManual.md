# PyTEDI User Manual

Prepared by **Alluvium** and **FlowMatters** for **Victorian Department of Energy, Environment and Climate Action**

November 2026

# Contents

- [PyTEDI Tool](#pytedi-tool)
  - [This manual](#this-manual)
  - [About the tool](#about-the-tool)
  - [How it works](#how-it-works)
  - [History](#history)
- [Installation](#installation)
  - [Required dependencies](#required-dependencies)
- [Using the code](#using-the-code)
  - [Reading a Windows STEDI model: check paths first](#reading-a-windows-stedi-model-check-paths-first)
  - [Reading a Windows STEDI model](#reading-a-windows-stedi-model)
  - [Reading a Windows STEDI model: advanced options](#reading-a-windows-stedi-model-advanced-options)
  - [Running the model](#running-the-model)
  - [Saving results](#saving-results)
  - [Saving the model](#saving-the-model)
  - [Opening a saved PyTEDI model](#opening-a-saved-pytedi-model)
  - [Other key features](#other-key-features)
    - [Historical scaling (method 1)](#historical-scaling-method-1)
    - [Historical scaling (method 2)](#historical-scaling-method-2)
    - [Variable start volumes](#variable-start-volumes)
    - [Variable dam surface areas](#variable-dam-surface-areas)
- [Package structure](#package-structure)
  - [Package files](#package-files)
  - [Key model attributes](#key-model-attributes)
- [References](#references)

# PyTEDI Tool

## This manual

This user manual provides guidance for usability and orientation of PyTEDI (Python Tool for Estimating Dam Impacts), commissioned by the Victorian Department of Energy, Environment and Climate Action (DEECA) and developed by Alluvium Consulting and FlowMatters in 2026.

## About the tool

PyTEDI is a Python tool for estimating catchment dam impacts on streamflow. Small catchment dams (also known as farm dams) are a key component of water resource models in Victoria and many other areas across Australia and the world. This tool calculates the impact of small dams on streamflows based on the TEDI (Tool for Estimating Dam Impacts) algorithm from the original paper by Nathan et al (2005), with several papers adding further to the data input methodology and calculation methods.

## How it works

PyTEDI uses the TEDI algorithm (Nathan et al., 2005), which is a water balance of each dam within a catchment. The tool assumes that the catchment is dendritic with all surface runoff draining to a single catchment outlet. Where farm dams are constructed, they intercept runoff. When the dam is full, it spills. When the dam is not full, it harvests all flow from its local upstream catchment.

A range of dam features are included in the tool, including summer bypasses, winterfill pumping, variable on-site demands, variable climate, and historical scaling over time.

## History

The original algorithm was developed and included in the Microsoft Windows based TEDI tool in 2001. TEDI was originally commissioned by DCNR (now DEECA), the Murray Darling Basin Commission, and Melbourne Water, and developed by Sinclair Knight Merz (now Jacobs). A review of TEDI some years later led to a software package called "Complete Hydrological Evaluation of the Assumptions of TEDI" (CHEAT). This, in turn, was later used for an upgraded version of TEDI called STEDI, where the 'S' referred to the spatial component of the tool where flow could be routed from one dam into another.

Commissioned by DSE (now DEECA) and developed by Sinclair Knight Merz, the first version of STEDI was released in 2009. The last formal update to STEDI was in 2012 (version 1.2), although some experimental versions were developed in 2013 (version 1.24) with a number of features included in response to specific issues observed in Queensland, northern NSW, and Western Australia. STEDI is owned jointly by Jacobs and DEECA. It is available for download from the Jacobs website.

In Victoria, STEDI is commonly used in conjunction with eWater Source water resource models. Unfortunately, the development of STEDI predates Source. This means that STEDI relies on file formats which are not supported by Source, and there is a need to improve the efficiency of Source workflows relating to farm dams. DEECA  specifically commissioned PyTEDI to address this need for efficiency, and to address a number of small bugs in STEDI.

# Installation

PyTEDI may be installed using pip like this:
```bash
pip install pytedi
```

It is also possible to install using wheel files downloaded from the repository directly, but only if you really know what you are doing. Pip is much easier.

## Required dependencies

PyTEDI requires Python 3.11–3.14. Python 3.11 or later is required because PyTEDI uses tomllib to read TOML configuration files, which was added to the Python standard library in Python 3.11.

PyTEDI requires a number of dependencies. These are automatically installed when PyTEDI is installed through pip. Most of the dependencies are standard in a relatively recent (circa 2026) Python environment. The key dependencies include:

- **Pandas** – needed for database handling (pandas.pydata.org)
- **NumPy** – needed for numerical handling (numpy.org)
- **Numba** – needed to make the code run fast (numba.readthedocs.io/en/stable)
- **tomllib** – needed to read text files (docs.python.org/dev/library/tomllib.html)

# Using the code

It is recommended that each modelling project has a separate working folder containing:

- the user script or notebook used to run PyTEDI;
- a separate folder for old STEDI input and output files (if available);
- a separate folder for PyTEDI model files, including parameters, timeseries, and damlist files; and
- a separate folder for outputs such as model results.

Alternatively, if you are working on several catchments, you could set up a modelling project with a separate folder for each catchment. 

A typical working folder may look like this:

```text
Project folder/
├── PythonScript_F1.py
├── STEDI/
│   ├── F1.scn
│   ├── F1_flow.fdy
│   ├── F1_rain.rdy
│   ├── F1_evap.edy
│   ├── other STEDI input files
│   └── other STEDI output files
├── pytedi/
│   ├── F1_params.scn
│   ├── F1_timeseries.csv
│   └── F1_damlist.csv
└── outputs/
    ├── F1_global_results.csv
    └── F1_individual_dam_results.csv
```
The working script can be saved in the main project folder. An example Python notebook is included in the installation package that contains examples of the PyTEDI functionality described in the sections below. This is called *pytedi_examples.ipynb*.

## Reading a Windows STEDI model: check paths first

PyTEDI includes functionality to read existing Windows STEDI scenario files. This allows users to convert and run historical STEDI model setups using the PyTEDI engine.

PyTEDI will read the file paths within the Windows STEDI .scn file to find the location of the input files. **STEDI model .scn files should be updated with the links to the working folder where files are located before running PyTEDI.** As a guide, STEDI models should be run-ready from the folder/directory they are located on your system.

For example, a STEDI model may include the following line:
```text
Input flow file:
Z:\Projects\Proj_12345\Technical\Farm Dams\Historic\Catch1\Catch1_Inflow.fdy
1
```
This means that the input flows can be found in column 1 of the stated file. But the path listed may not be suitable for the current project! Make the folder correct, for example:
```text
Input flow file:
G:\new\path\Catch1_Inflow.fdy
1
```

**Note that if PyTEDI can't find a STEDI input file at the stated path, it will also look in the same folder as the scenario file.**

## Reading a Windows STEDI model

The key function for reading an existing Windows STEDI scenario is `open_windows_STEDI_scenario()`. This function reads the scenario file, processes the input data, and returns a PyTEDI model object.
```python
import pytedi
import pandas as pd

scn_file = r'data\Example_STEDI_scenario.scn'

mymodel = pytedi.open_windows_STEDI_scenario(scn_file)
```
The `open_windows_STEDI_scenario()` function returns an instance of the PyTEDI `tedimodel` class. This object contains the model inputs, processed timeseries data, dam list, model settings and output dataframes.

## Reading a Windows STEDI model: advanced options

Many Windows STEDI models are defined using a distribution of farm dams. Such a distribution is specified as a histogram, for example with 10% of dams between 0 and 5 ML, 15% of dams between 5 and 10 ML, and so on. When models are defined in this way, STEDI uses the distribution to randomly generate a list of dams. This is problematic because the random number generator within PyTEDI produces different numbers, and therefore a different list of dams.

The standard function to read a Windows STEDI scenario file is `open_windows_STEDI_scenario()`.

This will read the scenario file including the information about the dam distribution. PyTEDI will then create a list of dams based on that distribution.

However, if PyTEDI is required to match STEDI more closely, it is possible to read a list of dams directly from a STEDI output file instead of the distribution from the scenario file. STEDI routinely produces output files listing all dams in the model regardless of how the dams were specified. By reading this output file, PyTEDI can use the exact list of dams in the STEDI model.

To read the list of dams from the STEDI output file, use the option `network_from_out` in the function, as follows:

```python
scn_file = r'data\Example_STEDI_scenario.scn'       # the STEDI scenario file
out_file = r'data\Example_STEDI_out.out'            # the STEDI output file containing the final list of dams

mymodel = pytedi.open_windows_STEDI_scenario(scn_file, network_from_out=out_file)

```

When randomly generating a list of dams from a distribution, the random number generator within PyTEDI has a fixed seed of 42, which means that the list of dams will be the same on every model run. However, users can vary the seed. This would allow users to generate _different_ lists of dams on each run, in order to quantify uncertainty within the dam distribution and how this affects streamflow.

To vary the seed of the random number generator, use the `seed` option in the function, as follows:

```python
scn_file = r'data\Example_STEDI_scenario.scn'
randomseed = 42
mymodel = pytedi.open_windows_STEDI_scenario(scn_file, seed = randomseed)
```

## Running the model

To run a PyTEDI model, use the `run_model` function as follows:
```python
mymodel.run_model()
```

Note that this command runs the model and saves results to a dataframe, but does not save outputs to file. Further commands are required to save outputs to a file.

## Saving results

PyTEDI can produce two types of model results files:

- **Global catchment results** – this includes all major fluxes within the overall catchment, such as inflows, outflows, demands, climate, etc.
- **Individual dam results** – this includes all major fluxes for each individual dam. Results for individual dams are only produced if they have been specifically flagged for output.

To write global catchment model results to a file, use the `save_results_global` function as follows:

```python
mymodel.save_results_global(r'output\Example_pytedi_catch_results.csv')
```

To export results for a specific farm dam of interest, we need to identify the dam first. By default, no individual dam results are produced:

```python
dam_number = 27      # this is the 27th dam in the "damlist"

mymodel.damlist.loc[dam_number,'output'] = 1       # set the 'output' flag to 1 to produce results

mymodel.run_model() # now run the model
mymodel.save_results_individual(r'output\Example_pytedi_indiv_results.csv')
```

This will save the selected dam's performance over the full time series.

## Saving the model

It is important to save the model so that it can be retrieved and re-run later. To save a PyTEDI model, use the `save_model` function as follows:

```python
model_file_prefix = (r'output\Example_pytedi_model')
mymodel.save_model(model_file_prefix)
```

This will save three model files as follows:

- **Model parameters** *(model_file_prefix + "\_params.scn")* – This contains all model parameters such as the model title, catchment area, and the names of the other two files. The file is saved in TOML format and is easily readable in any text editor such as notepad.
- **Dam list** *(model_file_prefix + "\_damlist.csv")* – This contains a comma separated list of all dams in the model and their characteristics.
- **Timeseries** *(model_file_prefix + "\_timeseries.csv")* – This contains all timeseries data for the model in comma separated format. This includes inflows, outflows, rainfall, evaporation, and demand patterns.

## Opening a saved PyTEDI model

To reopen a PyTEDI model saved using `save_model()`—see [Saving the model](#saving-the-model)—use `open_pytedi_scenario()` as follows:

```python
parameter_file = (r'output\Example_pytedi_model_params.scn')
mymodel2 = open_pytedi_scenario(parameter_file) # opens the model and assigns it to 'mymodel2'
```

Note that opening the parameter file will automatically open the dam list file and the timeseries file as well.

## Other key features

PyTEDI has several important features including two methods of historical scaling, variable start volumes, and variable dam surface areas.

### Historical scaling (method 1)

The `histoscale` dataframe represents changes in the effective level of dam development over time. PyTEDI applies the scaling within the water-balance calculations, including effective capacity, surface area and demand, rather than multiplying the final dam-impact results by a scaling factor.

By default, historical scaling is set to 1.0 (ie. no scaling) from 1 January 1800 to 1 January 2100. To modify the default values, change the `histoscale` attribute as follows:

```python
histdates = ['1965-01-01', '1990-01-01', '2010-01-01', '2030-01-01']   # 1965, 1990, 2010, and 2030
histdates = pd.DatetimeIndex(histdates)

histvalues = [0.0, 0.4, 1.0, 1.0]                                 # 0% in 1950, 40% in 1990, 100% in 2010 onwards

mymodel2.histoscale = pd.DataFrame(data=histvalues,index=histdates, columns=['histoscale'], dtype='float64')

mymodel2.run_model()                                               # now run the model
```

### Historical scaling (method 2)

The construction and decommissioning dates of each dam can be defined, so that the dam is considered to have zero volume and zero surface area before construction or after decommissioning.

By default, all dams are assumed to be constructed on 1 Jan in the year 0, and decommissioned on 1 Jan in the year 9999.

Note that when a dam is decommissioned, any water held in the dam will be spilled on 1st January.

To set the dates, use the `year_start` and `year_end` fields in the dam list.

```python
mymodel2.damlist.loc[5,'year_start'] = 1984      # sets the construction date of dam number 5 to 1984

mymodel2.damlist.loc[12,'year_end'] = 2003       # sets the decommission date of dam number 12 to 2003

mymodel2.damlist.loc[:,'year_start'] = 1965      # sets the construction date of all dams to 1965
```

It is possible to use the construction dates together with the histoscale feature, but it is not recommended.

### Variable start volumes

By default, the older Windows STEDI tool assumes all dams begin the model **completely empty**. This is the default in PyTEDI too, but can be varied by the user.

To vary the start volume, the `startstore_propfull` attribute can be set to any number between 0 and 1. For example:

```python
mymodel2.startstore_propfull = 0.5            # sets all dams to start 50% full

mymodel2.startstore_propfull = 1.0            # sets all dams to start 100% full
```

### Variable dam surface areas

By default, PyTEDI assumes that the surface area of a dam is the maximum as specified in the dam list. This means that the maximum surface area is assumed for all rainfall and evaporation calculations.

This behaviour is controlled by the `vary_surfarea` attribute which is set to `False` by default. 

To switch on variable surface areas, set `vary_surfarea` attribute to `True`. This will change the calculations so that the surface area of each dam is calculated based on a volume-to-surface area equation given by the parameters a and b as follows:

$$
\text{Volume (ML)} = a \left[\text{Surface area (m}^2\text{)}\right]^b
$$

By default, a = 0.0001042 and b = 1.3213 as given in Fowler et al. (2015).
This example shows how to set the model to vary surface areas and change the equation parameters.

```python
mymodel2.vary_surfarea = True               # sets surface areas to be calculated dynamically

mymodel2.vol_surfarea_a = 0.000145          # as per Lowe et al. (2005)
mymodel2.vol_surfarea_b = 1.314             # as per Lowe et al. (2005)
```

# Package structure

## Package files

The PyTEDI tool consists of a set of Python scripts containing the core model, set up as a class, and various functions, that are called from a user defined Python script or notebook.

**PyTEDI**

| **File** | **Description** |
| -------------- | ------------------------------------------------------------------------------------------- |
| \_\_init\_\_.py | This code initialises a new session when the PyTEDI model is called. |
| config.py     | Metadata about the PyTEDI model.     |
| main.py       | This code defines the class *tedimodel* which defines the blueprint of the model that is called to run PyTEDI. It also defines methods such as *open_windows_STEDI_scenario* and *open_pytedi_scenario*, *save_model*. |
| data_io.py    | These are the functions for reading and writing model data in a native PyTEDI format. |
| scenario.py   | Users can convert old Windows STEDI files for use with PyTEDI. These are the routines for reading old Windows scenario files. |
| damslist.py   | This is where information from a Windows STEDI file is interpreted to create a list of dams. |
| demands.py    | This is where information from a Windows STEDI file is interpreted to create demand information. |
| climate.py    | This is where information from a Windows STEDI file is interpreted to create climate and inflow data. |
| bypasses.py   | This is where information from a Windows STEDI file is interpreted to set up bypasses and winterfill. |
| engine.py     | This is the TEDI engine where the timestep calculations are done. |

## Key model attributes

The following list contains key PyTEDI model attributes that can be used to explore PyTEDI models and further explore functionality.

| **Attribute**       | **Data type**     | **Description**                                                                                                                                                                                |
| ------------------- | ------------------| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| title               | _String_          | The unique name or identifier for the model scenario run (e.g., 'Avoca River historic 1975-2026'). |
| timestep            | _String_          | The temporal resolution for climate inputs, streamflow routing, and water demands. Accepted values are 'day' or 'month'. |
| calc_nat_or_obs     | _String_          | Determines the mathematical direction of the water balance calculation.<br><br>Setting this to `obs` runs the model in the downstream direction, which takes natural upstream inflows as a model input and routes them downstream through the dams to estimate impacted flows.<br><br>Setting this to `nat` runs the model in the upstream direction, which takes observed flows downstream of the dams as a model input and routes them upstream through the dams to estimate what the flows upstream of the dams must be.<br><br>Note that the `nat` option (calculating natural flow given observed) uses a bisection algorithm to iteratively solve for the upstream flow. For this reason, the `nat` option will take slightly longer to run. |
| cat_area_km2        | _Float_           | The total contributing surface area of the study catchment in square kilometres (km<sup>2</sup>). |
| damlist             | _dataframe_       | List of dams in the catchment and their characteristics. Depending on initial configuration settings, this dataframe can be populated in two distinct ways. If an explicit scenario file contains individual dam records, the table maps the exact physical properties and geographic network connections for every real-world dam in the catchment. If individual details are omitted, PyTEDI populates this Dataframe by sampling from pre-assigned regional dam distributions to approximate the catchment's overall characteristics. |
| ts                  | _dataframe_       | Timeseries of demand, climate, and flow. |
| scale_limit         | _Float_           | The upper limit of the ratio of impounded area to total area, defaulting to 0.8.<br><br>It has been found that when the impounded area is more than 80% of the total catchment, the model can become unstable when there is high rainfall and runoff on a single timestep. To avoid this instability, the ratio of impounded area to total area is automatically reviewed before the model is run. If the ratio is greater than scale_limit, the catchment area upstream of all dams will be adjusted down so that the ratio is equal to scale_limit.  |
| histoscale          | _dataframe_       | Where necessary, outputs can be scaled over time to represent historic increases in levels of development.<br><br>By default, the scaling is set to 1 (constant) as follows: <br>1800-01-01 = 1.0 <br>2100-01-01 = 1.0<br><br>A historical scaling pattern could be as follows: <br>1950-01-01 = 0.0 <br>2000-01-01 = 0.9 <br>2010-01-01 = 1.0 <br>2030-01-01 = 1.0 |
| vol_surfarea_a <br>vol_surfarea_b | _Float_           | Power-law scaling relationship coefficients used to calculate a dam's full capacity volume based on its surface area footprint. The default values are based on Fowler et al. (2015). |
| startstore_propfull | _Float_           | The initial volume of water held across all dams at timestep zero, expressed as a fraction of maximum capacity. Default is 0.0, as STEDI v1.2 defaults to 0.0. To start with storages 100% full, use 1.0. |
| rundate             | _Datetime_        | A time-stamped log marking exactly when the simulation engine was last executed. Evaluates to `NaN` if the model has not been run yet. |
| catch_results       | _dataframe_       | A dataframe storing final water balance fluxes for the overall catchment. The dataframe will be empty if the model has not been run yet. |
| indiv_results       | _dataframe_       | A timeseries of water balance fluxes for individual dams, only those marked by a 1 in the `output` field in the damlist. If no dams have been marked with a 1 in the output field, this dataframe will be empty. Also, it will be empty if the model has not been run yet. |
| stedi_params        | _dict_            | A list of all of the parameters read from a Windows STEDI scenario file. This is only populated when a Windows STEDI scenario file has been read. |
| pyparams       | _dict_            | A list of all of the parameters read from a PyTEDI scenario file. This is only populated when a PyTEDI scenario file has been read. |

# References

Fowler, K., Morden, R., Lowe, L., Nathan, R., 2015. Advances in assessing the impact of hillside farm dams on streamflow. Australian Journal of Water Resources 19. <https://doi.org/10.1080/13241583.2015.1116182>

Morden, R., 2017. A new method of accounting for runoff dams, in: Syme, G., Hatton MacDonald, D., Fulton, B., Piantadosi, J. (Eds.), MODSIM2017, 22nd International Congress on Modelling and Simulation. Hobart, Australia, pp. 1676–1682. <https://doi.org/10.36334/MODSIM.2017.L8.morden>

Nathan, R., Jordan, P., Morden, R., 2005. Assessing the impact of farm dams on streamflows, Part I: Development of Simulation Tools. Australian Journal of Water Resources 9, 1–12. <https://doi.org/10.1080/13241583.2005.11465259>

Nathan, R., Lowe, L., 2012. The hydrologic impacts of farm dams. Australasian Journal of Water Resources 16, 75–83. <https://doi.org/10.7158/13241583.2012.11465405>
