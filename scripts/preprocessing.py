# %% imports
import os
from pathlib import Path
import numpy as np
import pandas as pd
import rioxarray as rxr
from scipy.special import gamma
from scipy.interpolate import interp1d
from ast import literal_eval

from config import ROOTDIR, turbines

# %% turbine power curves
# renewables ninja
rnj_power_curves = pd.read_csv(ROOTDIR / 'data/power_curves/rnj_power_curve_000-smooth.csv')
# open energy platform --
oep_power_curves = pd.read_csv(ROOTDIR / 'data/power_curves/supply__wind_turbine_library.csv')
oep_power_curves['type_string'] = oep_power_curves['manufacturer'] + '.' + oep_power_curves['turbine_type'].replace({'/': '.', '-': ''}, regex=True)
oep_power_curves.dropna(subset=['power_curve_values'], inplace=True)
# nrel
nrel_power_curves = pd.read_csv(ROOTDIR / 'data/power_curves/sam_wind_turbines.csv', header=[0, 1, 2])
nrel_power_curves['Wind Speed Array'].replace('|', ',')

# process power curves
u_pwrcrv = np.linspace(0.5, 30, num=60)
powercurves = pd.DataFrame(index=u_pwrcrv)

missing_turbs = []
for turbine, _ in turbines.items():
    if oep_power_curves['type_string'].str.contains(turbine).any():
        sel = oep_power_curves['type_string'].str.contains(turbine)
        n = oep_power_curves[sel].index[0]
        f_itpl = interp1d(literal_eval(oep_power_curves.loc[n, 'power_curve_wind_speeds']),
                          literal_eval(oep_power_curves.loc[n, 'power_curve_values']) / oep_power_curves.loc[
                              n, 'nominal_power'], kind='linear', bounds_error=False, fill_value=0)
        powercurves[oep_power_curves.loc[n, 'type_string']] = f_itpl(u_pwrcrv)
    elif turbine in rnj_power_curves.columns:
        f_itpl = interp1d(rnj_power_curves['speed'], rnj_power_curves[turbine], kind='linear')
        powercurves[turbine] = f_itpl(u_pwrcrv)
    else:
        missing_turbs.append(turbine)
powercurves.index.name = 'speed'

if not os.path.exists(ROOTDIR / 'data/preprocessed'):
    os.mkdir(ROOTDIR / 'data/preprocessed')

powercurves.to_csv(ROOTDIR / 'data/preprocessed/powercurves.csv', sep=';', decimal=',')

# %% compute air density correction factor from elevation data
elevation = rxr.open_rasterio(ROOTDIR / 'data/gwa3/AUT_elevation_w_bathymetry.tif')

# compute air density correction
# see https://wind-data.ch/tools/luftdichte.php
rho_correction = 1.247015 * np.exp(-0.000104 * elevation) / 1.225
rho_correction.to_netcdf(path=ROOTDIR / 'data/preprocessed/gwa_air_density.nc')

# %% compute roughness factor alpha
# read Weibull parameters at different heights
a50 = rxr.open_rasterio(ROOTDIR / 'data/gwa3/AUT_combined-Weibull-A_50.tif')
k50 = rxr.open_rasterio(ROOTDIR / 'data/gwa3/AUT_combined-Weibull-k_50.tif')
u_mean_50 = a50 * gamma(1 / k50 + 1)

a100 = rxr.open_rasterio(ROOTDIR / 'data/gwa3/AUT_combined-Weibull-A_100.tif')
k100 = rxr.open_rasterio(ROOTDIR / 'data/gwa3/AUT_combined-Weibull-k_100.tif')
u_mean_100 = a100 * gamma(1/k100 + 1)

# calculate roughness factor alpha for each pixel and rescale to coordinates of A and k data grid
alpha = (np.log(u_mean_100) - np.log(u_mean_50)) / (np.log(100) - np.log(50))
alpha.to_netcdf(path=ROOTDIR / 'data/preprocessed/gwa_roughness.nc', mode='w', format='NETCDF4', engine='netcdf4')
