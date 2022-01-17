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
    ROOTDIR = Path('c:/git_repos/impax')
else:
    ROOTDIR = Path('d:/git_repos/boud')

# read A and k parameters of windspeed Weibull distribution from Austrian wind atlas
A100 = rxr.open_rasterio(ROOTDIR / 'data/gwa3/AUT_combined-Weibull-A_100.tif')
A100 = A100.squeeze()

k100 = rxr.open_rasterio(ROOTDIR / 'data/gwa3/AUT_combined-Weibull-k_100.tif')
k100 = k100.squeeze()

# read preprocessed data
alpha = xr.open_dataarray(ROOTDIR / 'data/preprocessed/gwa_roughness.nc')
alpha = alpha.squeeze()
rho = xr.open_dataarray(ROOTDIR / 'data/preprocessed/gwa_air_density.nc')
rho = rho.squeeze()
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
