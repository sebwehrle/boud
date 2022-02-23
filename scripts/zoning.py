# %% imports
from pathlib import Path
import numpy as np
import xarray as xr
import gamstransfer as gt
import geopandas as gpd
from config import ROOTDIR
from src.funs import sliced_location_optimization, locations_to_gdf

import matplotlib.pyplot as plt

# %%
gams_dict = {
    'gams_model': ROOTDIR / 'opt/location_selection.gms',
    'gdx_input': ROOTDIR / 'opt/input_data.gdx',
    'gdx_output': ROOTDIR / 'opt',
    'gams_exe': Path('c:/myprogs/gams/37')
}

# %% define functions
def array_clip(data_array, gdf):
    clipped = data_array.rio.clip(gdf.geometry, gdf.crs, drop=True, invert=False, all_touched=True)
    if '_FillValue' in data_array.attrs:
        clipped = clipped.where(clipped != clipped._FillValue)
    return clipped


# %% read data
# read state borders
vgd = gpd.read_file(ROOTDIR / 'data/vgd/VGD.shp')
states = vgd[['BL', 'geometry']].dissolve(by='BL')
states.reset_index(inplace=True)

clc = gpd.read_file(ROOTDIR / 'data/clc/CLC18_AT_clip.shp')
clc['CODE_18'] = clc['CODE_18'].astype('int')
clc = clc[clc['CODE_18'] <= 121]
clc = clc.to_crs(states.crs)
clc = clc.buffer(500)

noe = gpd.read_file(ROOTDIR / 'data/zones/RRU_WIND_ZONEN_P19Polygon.shp')
noe = noe.to_crs(clc.crs)

bgld = gpd.read_file(ROOTDIR / 'data/zones/BGLD_FLAECHENWIDMUNG.shp')
bgld = bgld.loc[bgld['BEZEICH'] == 'Windkraftanlage', 'geometry']
bgld = bgld.to_crs(clc.crs)

stmk = gpd.read_file(ROOTDIR / 'data/zones/SAPRO_Windenergie_zone.shp')
stmk = stmk.loc[stmk['Zone'] == 'Vorrang', 'geometry']
stmk = stmk.to_crs(clc.crs)

# zones = stmk.loc[stmk['Zone'] == 'Vorrang', 'geometry']
# zones = zones.append(noe['geometry'])
# zones = zones.append(bgld.loc[bgld['BEZEICH'] == 'Windkraftanlage', 'geometry'])
# zones = zones.reset_index(drop=True)

lcoe = xr.open_dataarray(ROOTDIR / 'data/results/lcoe_hoeltinger.nc', mask_and_scale=True)
lcoe = lcoe.min(dim='turbine_models')
lcoe = lcoe.rio.reproject(clc.crs)
clipped = lcoe.rio.clip(clc.geometry, clc.crs, drop=False, invert=True)
clipped = clipped.where(clipped != clipped._FillValue)

energy = xr.open_dataarray(ROOTDIR / 'data/results/energy_generation.nc')
energy = energy.drop_vars('turbine_models')
energy = energy.rio.reproject(clc.crs)
power = xr.open_dataarray(ROOTDIR / 'data/results/installed_power.nc')
power = power.rio.write_crs('epsg:3416')
power = power.rio.reproject(clc.crs)

# clip_all = clipped.rio.clip(zones.geometry, zones.crs, drop=True, invert=False)
noe_clip = array_clip(clipped, noe)
bgld_clip = array_clip(clipped, bgld)
stmk_clip = array_clip(clipped, stmk)

# %% Optimize turbine locations in zoning areas
read_only = False
cont = gt.Container()

spacing = 3

# Lower Austria
loca_noe = sliced_location_optimization(gams_dict, cont, noe_clip, num_slices=1, space_px=spacing, num_turbines=np.floor(1506/3),  # 4930,
                                        gdx_out_string='zones_noe', read_only=read_only)
lcoe_noe_zone = locations_to_gdf(noe_clip, loca_noe, energy_array=array_clip(energy, noe),
                                 power_array=array_clip(power, noe))

# Burgenland
loca_bgld = sliced_location_optimization(gams_dict, cont, bgld_clip, num_slices=1, space_px=spacing, num_turbines=np.floor(347/3),  # 925,
                                         gdx_out_string='zones_bgld', read_only=read_only)
lcoe_bgld_zone = locations_to_gdf(bgld_clip, loca_bgld, energy_array=array_clip(energy, bgld),
                                  power_array=array_clip(power, bgld))

# Styria
loca_stmk = sliced_location_optimization(gams_dict, cont, stmk_clip, num_slices=1, space_px=spacing, num_turbines=np.floor(265/3),  # 820,
                                         gdx_out_string='zones_stmk', read_only=read_only)
lcoe_stmk_zone = locations_to_gdf(stmk_clip, loca_stmk, energy_array=array_clip(energy, stmk),
                                  power_array=array_clip(power, stmk))

# %% optimize LCOE for any location in Lower Austria
read_only = True

noe_any_clip = clipped.rio.clip(states[states.BL == 'Niederösterreich'].geometry, states.crs, drop=True, invert=False)
noe_any_clip = noe_any_clip.where(noe_any_clip != noe_any_clip._FillValue)
loca_noe_any = sliced_location_optimization(gams_dict, cont, noe_any_clip, num_slices=1, space_px=spacing,
                                            num_turbines=1506, gdx_out_string='any_noe', read_only=read_only)  # 4930
lcoe_noe_any = locations_to_gdf(noe_any_clip, loca_noe_any,
                                energy_array=array_clip(energy, states[states.BL == 'Niederösterreich']),
                                power_array=array_clip(power, states[states.BL == 'Niederösterreich']))

bgld_any_clip = clipped.rio.clip(states[states.BL == 'Burgenland'].geometry, states.crs, drop=True, invert=False)
bgld_any_clip = bgld_any_clip.where(bgld_any_clip != bgld_any_clip._FillValue)
loca_bgld_any = sliced_location_optimization(gams_dict, cont, bgld_any_clip, num_slices=1, space_px=spacing,
                                             num_turbines=347, gdx_out_string='any_bgld', read_only=read_only)  # 925
lcoe_bgld_any = locations_to_gdf(bgld_any_clip, loca_bgld_any,
                                 energy_array=array_clip(energy, states[states.BL == 'Burgenland']),
                                 power_array=array_clip(power, states[states.BL == 'Burgenland']))

stmk_any_clip = clipped.rio.clip(states[states.BL == 'Steiermark'].geometry, states.crs, drop=True, invert=False)
stmk_any_clip = stmk_any_clip.where(stmk_any_clip != stmk_any_clip._FillValue)
loca_stmk_any = sliced_location_optimization(gams_dict, cont, stmk_any_clip, num_slices=1, space_px=spacing,
                                             num_turbines=265, gdx_out_string='any_stmk', read_only=read_only)  # 820
lcoe_stmk_any = locations_to_gdf(stmk_any_clip, loca_stmk_any,
                                 energy_array=array_clip(energy, states[states.BL == 'Steiermark']),
                                 power_array=array_clip(power, states[states.BL == 'Steiermark']))

# %% plot LCOE in zones versus LCOE in all of Lower Austria


def xy_plot(x1, x2, y1, y2, label1, label2, ylim, ylabel, xlabel, title, savepath):
    fig, ax = plt.subplots(1, 1)
    plt.plot(x1, y1, color='blue', label=label1)
    plt.plot(x2, y2, color='green', label=label2)
    ax.set_ylim(ylim)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    plt.title(title)
    plt.legend()
    plt.grid()
    plt.savefig(savepath)
    plt.show()
    plt.close()


fig_string = 'zoning_hoeltinger_sparse'
ylim = [60, 200]

xy_plot(lcoe_noe_zone['Power'].cumsum()/1000, lcoe_noe_any['Power'].cumsum()/1000, lcoe_noe_zone['LCOE'],
        lcoe_noe_any['LCOE'], 'Zones', 'Unrestricted', ylim, 'LCOE [€/MWh]',
        'Installed Capacity [MW]', 'Lower Austria', ROOTDIR / f'figures/NOe_OC_power_{fig_string}.pdf')

xy_plot(lcoe_noe_zone['Energy'].cumsum()/1000, lcoe_noe_any['Energy'].cumsum()/1000, lcoe_noe_zone['LCOE'],
        lcoe_noe_any['LCOE'], 'Zones', 'Unrestricted', ylim, 'LCOE [€/MWh]', 'Wind power generation [TWh]',
        'Lower Austria', ROOTDIR / f'figures/NOe_OC_energy_{fig_string}.pdf')

xy_plot(lcoe_stmk_zone['Power'].cumsum()/1000, lcoe_stmk_any['Power'].cumsum()/1000, lcoe_stmk_zone['LCOE'],
        lcoe_stmk_any['LCOE'], 'Zones', 'Unrestricted', ylim, 'LCOE [€/MWh]', 'Installed Capacity [MW]',
        'Styria', ROOTDIR / f'figures/Stmk_OC_power_{fig_string}.pdf')

xy_plot(lcoe_stmk_zone['Energy'].cumsum()/1000, lcoe_stmk_any['Energy'].cumsum()/1000, lcoe_stmk_zone['LCOE'],
        lcoe_stmk_any['LCOE'], 'Zones', 'Unrestricted', ylim, 'LCOE [€/MWh]', 'Wind power generation [TWh]',
        'Styria', ROOTDIR / f'figures/Stmk_OC_energy_{fig_string}.pdf')

xy_plot(lcoe_bgld_zone['Power'].cumsum()/1000, lcoe_bgld_any['Power'].cumsum()/1000, lcoe_bgld_zone['LCOE'],
        lcoe_bgld_any['LCOE'], 'Zones', 'Unrestricted', ylim, 'LCOE [€/MWh]', 'Installed Capacity [MW]',
        'Burgenland', ROOTDIR / f'figures/Bgld_OC_power_{fig_string}.pdf')

xy_plot(lcoe_bgld_zone['Energy'].cumsum()/1000, lcoe_bgld_any['Energy'].cumsum()/1000, lcoe_bgld_zone['LCOE'],
        lcoe_bgld_any['LCOE'], 'Zones', 'Unrestricted', ylim, 'LCOE [€/MWh]', 'Wind power generation [TWh]',
        'Burgenland', ROOTDIR / f'figures/Bgld_OC_energy_{fig_string}.pdf')


# %%
fig, ax = plt.subplots(1, 1)
lcoe_noe_zone['LCOE'].plot(ax=ax, color='blue', label='Zones')
lcoe_noe_any['LCOE'].plot(ax=ax, color='green', label='Unrestricted')
ax.set_ylim([18, 120])
ax.set_ylabel('LCOE [€/MWh]')
ax.set_xlabel('Wind turbine generation [TWh]')
plt.title('Lower Austria')
plt.legend()
plt.grid()
plt.savefig(ROOTDIR / 'figures/NOe_OC_zoning_nogridcost.pdf')
plt.show()

fig, ax = plt.subplots(1, 1)
lcoe_bgld_zone['LCOE'].plot(ax=ax, color='blue', label='Zones')
lcoe_bgld_any['LCOE'].plot(ax=ax, color='green', label='Unrestricted')
ax.set_ylim([18, 60])
ax.set_ylabel('LCOE [€/MWh]')
ax.set_xlabel('Wind turbine locations')
plt.title('Burgenland')
plt.legend()
plt.grid()
plt.savefig(ROOTDIR / 'figures/Bgld_OC_zoning_nogridcost.pdf')

fig, ax = plt.subplots(1, 1)
lcoe_stmk_zone['LCOE'].plot(ax=ax, color='blue', label='Zones')
lcoe_stmk_any['LCOE'].plot(ax=ax, color='green', label='Unrestricted')
ax.set_ylim([18, 60])
ax.set_ylabel('LCOE [€/MWh]')
ax.set_xlabel('Wind turbine locations')
plt.title('Styria')
plt.legend()
plt.grid()
plt.savefig(ROOTDIR / 'figures/Stmk_OC_zoning_nogridcost.pdf')


# %% plot zones versus optimized turbine locations
fig, ax = plt.subplots(1, 1)
noe.boundary.plot(ax=ax, zorder=1, color='red')
lcoe_noe_zone.plot(ax=ax, zorder=2, color='blue', markersize=1)
plt.show()

fig, ax = plt.subplots(1, 1)
bgld.boundary.plot(ax=ax, zorder=1, color='red')
lcoe_bgld_zone.plot(ax=ax, zorder=2, color='blue', markersize=1)
plt.show()

fig, ax = plt.subplots(1, 1)
stmk.boundary.plot(ax=ax, zorder=1, color='red')
lcoe_stmk_zone.plot(ax=ax, zorder=2, color='blue', markersize=1)
plt.show()

# %% zoom-plot of sited turbines and lcoe map

fig, ax = plt.subplots(1, 1, figsize=(8, 9))
lcoe.sel(y=slice(457000, 451000), x=slice(624000, 629000)).plot(ax=ax, zorder=1)
lcoe_noe_zone.plot(ax=ax, zorder=2, color='red')
plt.tight_layout()
plt.show()
