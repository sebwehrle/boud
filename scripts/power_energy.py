# %% imports
import xarray as xr
from config import ROOTDIR, turbines

# %% read data
cf = xr.open_dataarray(ROOTDIR / 'data/preprocessed/capacity_factors.nc')
cf = cf.rio.reproject('epsg:3416')
lcoe = xr.open_dataarray(ROOTDIR / 'data/results/lcoe.nc')

# calculate power per pixel in LCOE optimum
lc_turbines = lcoe.idxmin(dim='turbine_models')
lc_idx = lcoe.fillna(999).argmin(dim='turbine_models')
power = lc_turbines.copy()
for name, char in turbines.items():
    power = xr.where(power == name, char[0], power)
power.data = power.data.astype('float')
power.to_netcdf(path=ROOTDIR / 'data/results/installed_power.nc', format='NETCDF4', engine='netcdf4')

lc_cf = cf.isel(turbine_models=lc_idx)

# energy per pixel = capacity_factor * power * hours_in_year / 1000
energy_giga = lc_cf * power * 8760 / 1000000
energy_giga.to_netcdf(path=ROOTDIR / 'data/results/energy_generation.nc', format='NETCDF4', engine='netcdf4')
