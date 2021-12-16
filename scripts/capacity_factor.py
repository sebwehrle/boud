# %% imports
from pathlib import Path
import numpy as np
import pandas as pd
import rioxarray as rxr
import xarray as xr
import matplotlib.pyplot as plt

from config import where, turbines
from src.funs import weibull_probability_density, capacity_factor


# %% read data
if where == 'home':
    ROOTDIR = Path('/')
else:
    ROOTDIR = Path('d:/git_repos/impax')

# read A and k parameters of windspeed Weibull distribution from Austrian wind atlas
A100 = rxr.open_rasterio(ROOTDIR / 'data/windatlas/a120_100m_Lambert.img')
A100 = A100.rio.reproject('EPSG:3416').squeeze()
A100.values[A100.values <= 0] = np.nan

k100 = rxr.open_rasterio(ROOTDIR / 'data/windatlas/k120_100m_Lambert.img')
k100 = k100.rio.reproject('EPSG:3416').squeeze()
k100.values[k100.values <= 0] = np.nan

# read preprocessed data
alpha = xr.open_dataarray(ROOTDIR / 'data/preprocessed/awa_roughness.nc')
rho = xr.open_dataarray(ROOTDIR / 'data/preprocessed/air_density.nc')
powercurves = pd.read_csv(ROOTDIR / 'data/preprocessed/powercurves.csv', sep=";", decimal=',')
u_pwrcrv = powercurves['speed'].values
powercurves.set_index('speed', drop=True, inplace=True)

# %% calculate weibull wind speed probability density
p = weibull_probability_density(u_pwrcrv, k100, A100)

#%% fold wind speed probability density and wind turbine power curve
cf_arr = []
for turbine_type in powercurves.columns:
    cf = capacity_factor(p, alpha, u_pwrcrv, powercurves[turbine_type].values,
                         h_turbine=turbines[turbine_type][1]) * rho
    cf_arr.append(cf)

cap_factors = xr.concat(cf_arr, dim='turbine_models')
cap_factors = cap_factors.assign_coords({'turbine_models': powercurves.columns.values})
cap_factors.to_netcdf(path=ROOTDIR / 'data/preprocessed/capacity_factors.nc', format='NETCDF4', engine='netcdf4')
cap_factors.close()
