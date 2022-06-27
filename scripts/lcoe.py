# %% imports
import os
import numpy as np
import pandas as pd
import xarray as xr

from config import ROOTDIR, turbines, country
from src.funs import turbine_overnight_cost, grid_connect_cost, levelized_cost

# %% settings
# year = 2016
availability = 0.85
fix_om = 20  # 20  # EUR/kW
var_om = 8  # 26.4  # 0.008 * 1000  # EUR/kWh
discount_rate = 0.04  # 0.05  # 0.03
lifetime = 20  # 25

# %% get data
# read capacity factors
cf = xr.open_dataarray(ROOTDIR / f'data/preprocessed/capacity_factors_{country}.nc')
cf = cf.rio.reproject('epsg:3416')
# read distances to grid
#dt = xr.open_dataset(ROOTDIR / f'data/preprocessed/grid_distance_{country}.nc')
#dt = dt.rio.write_crs('epsg:3416')
# read power curves
powercurves = pd.read_csv(ROOTDIR / 'data/preprocessed/powercurves.csv', sep=';', decimal=',')

# %% calculation of LCOE
LCOE = []
onc = []
for key, value in turbines.items():
    if key in powercurves.columns:
        power = value[0]/1000
        hub_height = value[1]
        rotor_diameter = value[2]
        overnight_cost = np.round(turbine_overnight_cost(power, hub_height, rotor_diameter, value[3]), 0)
        onc.append(overnight_cost)
        capacity_factor = cf.sel(turbine_models=key)
        lcoe = levelized_cost(capacity_factor, overnight_cost, grid_connect_cost(power*1000), fix_om, var_om, discount_rate, lifetime)
                              # overnight_cost, grid_cost, fix_om, var_om, discount_rate, lifetime)
        LCOE.append(lcoe)
    else:
        pass

lcoe = xr.concat(LCOE, dim='turbine_models')

dir_results = ROOTDIR / 'data/results'
if not os.path.exists(dir_results):
    os.mkdir(dir_results)
lcoe.to_netcdf(dir_results / f'lcoe_{country}.nc')

