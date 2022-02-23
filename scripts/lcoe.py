# %% imports
import os
import pandas as pd
import xarray as xr

from config import ROOTDIR, turbines
from src.funs import turbine_overnight_cost, grid_invest_cost, levelized_cost

# %% settings
# year = 2016
availability = 0.85
fix_om = 0  # 20  # EUR/kW
var_om = 26.4  # 0.008 * 1000  # EUR/kWh
discount_rate = 0.05  # 0.03
lifetime = 20  # 25

# %% get data
# read capacity factors
cf = xr.open_dataarray(ROOTDIR / 'data/preprocessed/capacity_factors.nc')
cf = cf.rio.reproject('epsg:3416')
# read distances to grid
dt = xr.open_dataset(ROOTDIR / 'data/preprocessed/grid_distance.nc')
dt = dt.rio.write_crs('epsg:3416')
# read power curves
powercurves = pd.read_csv(ROOTDIR / 'data/preprocessed/powercurves.csv', sep=';', decimal=',')

# %% calculation of LCOE
grid_cost = grid_invest_cost(dt)

LCOE = []
onc = []
for key, value in turbines.items():
    if key in powercurves.columns:
        power = value[0]/1000
        hub_height = value[1]
        rotor_diameter = value[2]
        overnight_cost = turbine_overnight_cost(power, hub_height, rotor_diameter, value[3]) * 1000
        onc.append(overnight_cost)
        capacity_factor = cf.sel(turbine_models=key)
        lcoe = levelized_cost(capacity_factor, 1675000, grid_cost, fix_om, var_om, discount_rate, lifetime)
                              # overnight_cost, grid_cost, fix_om, var_om, discount_rate, lifetime)
        LCOE.append(lcoe)
    else:
        pass

lcoe = xr.concat(LCOE, dim='turbine_models')

dir_results = ROOTDIR / 'data/results'
if not os.path.exists(dir_results):
    os.mkdir(dir_results)
lcoe.to_netcdf(dir_results / 'lcoe_hoeltinger.nc')

