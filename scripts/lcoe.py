from pathlib import Path
import pandas as pd
import xarray as xr
import rioxarray as rxr

from config import where, turbines
from src.funs import turbine_overnight_cost, grid_invest_cost, levelized_cost

# %% settings
year = 2016
availability = 0.85
fix_om = 20  # EUR/kW
var_om = 0.008 * 1000  # EUR/kWh
discount_rate = 0.03
lifetime = 25

# %% get data
if where == 'home':
    ROOTDIR = Path('c:/git_repos/impax')
else:
    ROOTDIR = Path('d:/git_repos/impax')

# %% read capacity factors
cf = xr.open_dataarray(ROOTDIR / 'data/preprocessed/capacity_factors.nc')
cf = cf.rio.reproject('epsg:3416')
# read distances to grid
dt = xr.open_dataset(ROOTDIR / 'data/preprocessed/grid_distance.nc')  #, drop_variables='spatial_ref')
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
        overnight_cost = turbine_overnight_cost(power, hub_height, rotor_diameter, year) * 1000
        onc.append(overnight_cost)
        capacity_factor = cf.sel(turbine_models=key)
        lcoe = levelized_cost(capacity_factor, availability, overnight_cost, grid_cost, fix_om, var_om, discount_rate, lifetime)
        LCOE.append(lcoe)
    else:
        pass

lcoe = xr.concat(LCOE, dim='turbine_models')
lcoe.to_netcdf(ROOTDIR / 'data/results/lcoe.nc')