# %% imports
import os
import numpy as np
import pandas as pd
import rioxarray as rxr
from scipy.special import gamma

from config import ROOTDIR, turbines, country
from src.utils import process_power_curves

# %% read data
rnj_power_curves = pd.read_csv(ROOTDIR / 'data/power_curves/rnj_power_curve_000-smooth.csv')
oep_power_curves = pd.read_csv(ROOTDIR / 'data/power_curves/supply__wind_turbine_library.csv')

elevation = rxr.open_rasterio(ROOTDIR / f'data/gwa3/{country}_elevation_w_bathymetry.tif')
a50 = rxr.open_rasterio(ROOTDIR / f'data/gwa3/{country}_combined-Weibull-A_50.tif')
k50 = rxr.open_rasterio(ROOTDIR / f'data/gwa3/{country}_combined-Weibull-k_50.tif')
a100 = rxr.open_rasterio(ROOTDIR / f'data/gwa3/{country}_combined-Weibull-A_100.tif')
k100 = rxr.open_rasterio(ROOTDIR / f'data/gwa3/{country}_combined-Weibull-k_100.tif')

# %% turbine power curves
oep_power_curves['type_string'] = oep_power_curves['manufacturer'] + '.' + oep_power_curves['turbine_type'].replace({'/': '.', '-': ''}, regex=True)
oep_power_curves.dropna(subset=['power_curve_values'], inplace=True)

powercurves = process_power_curves(turbines, rnj_power_curves, oep_power_curves)

if not os.path.exists(ROOTDIR / 'data/preprocessed'):
    os.mkdir(ROOTDIR / 'data/preprocessed')
powercurves.to_csv(ROOTDIR / 'data/preprocessed/powercurves.csv', sep=';', decimal=',')

# %% compute air density correction factor from elevation data
# compute air density correction - see https://wind-data.ch/tools/luftdichte.php
rho_correction = 1.247015 * np.exp(-0.000104 * elevation) / 1.225
rho_correction.to_netcdf(path=ROOTDIR / f'data/preprocessed/gwa_air_density_{country}.nc')

# %% compute roughness factor alpha
u_mean_50 = a50 * gamma(1 / k50 + 1)
u_mean_100 = a100 * gamma(1/k100 + 1)
alpha = (np.log(u_mean_100) - np.log(u_mean_50)) / (np.log(100) - np.log(50))
alpha.to_netcdf(path=ROOTDIR / f'data/preprocessed/gwa_roughness_{country}.nc',
                mode='w', format='NETCDF4', engine='netcdf4')
