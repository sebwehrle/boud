# boud

Benefits of undisturbed landscapes -- estimating the opportunity cost of wind turbine placement in Austria

## Data requirements
All data can be downloaded through the script `data_download.py`.

### Preprocessing
* Wind turbine power curves: renewables.ninja's [virtual wind farm](https://github.com/renewables-ninja/vwf)
and [open energy platform](https://openenergy-platform.org/dataedit/view/supply/wind_turbine_library).
* Roughness: average wind speeds at 50m and 100m height on a 250m raster from the [Global wind atlas](https://globalwindatlas.info/download/gis-files).
* Air density: Digital terrain model of Austria from the global wind atlas [Global wind atlas](https://globalwindatlas.info/download/gis-files). 

[//]: # (* Digital terrain model on 10m x 10m grid from [Open Data Österreich / Land Kärnten]&#40;https://www.data.gv.at/katalog/dataset/d88a1246-9684-480b-a480-ff63286b35b7&#41;.)

### Distance to grid
* High voltage grid lines: extracted from [grid kit Europe](https://zenodo.org/record/47317#.YbrxolkxkQ8).
* Austrian borders: [Open Data Österreich / Bundesamt für Eich- und Vermessungswesen](https://www.data.gv.at/katalog/dataset/bev_verwaltungsgrenzenstichtagsdaten150000/resource/61eb4777-3d0e-4328-8a8b-a04b24ecdbba)
* Settlements: [Corine Land Cover 2018](https://www.data.gv.at/katalog/dataset/76617316-b9e6-4bcd-ba09-e328b578fed2).

### Capacity factors
* Wind speeds: Parameters of the Weibull distribution of hourly mean wind speeds at 100m height on a 250m x 250m raster 
of the [Global wind atlas](https://www.globalwindatlas.info/download/gis-files).

### Levelized cost of electricity
* Wind turbine overnight cost from [Rinne et al.](https://doi.org/10.1038/s41560-018-0137-9)

## Replication
For the time being, replicating the results requires to run the scripts in the following order:
1) [`data_download.py`](https://github.com/sebwehrle/boud/blob/main/scripts/data_download.py)
2) [`preprocessing.py`](https://github.com/sebwehrle/boud/blob/main/scripts/preprocessing.py)
3) [`distances.py`](https://github.com/sebwehrle/boud/blob/main/scripts/distances.py)
4) [`capacity_factor.py`](https://github.com/sebwehrle/boud/blob/main/scripts/capacity_factor.py)
5) [`lcoe.py`](https://github.com/sebwehrle/boud/blob/main/scripts/lcoe.py)
6) [`power_energy.py`]()

`zoning.py` is based on these results and calculates optimal spacing of turbines with a 500m radius within 
wind power zones in Lower Austria, Styria and Burgenland as well as in the whole state.

