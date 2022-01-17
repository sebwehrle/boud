# %% imports
# import os
from pathlib import Path
# import numpy as np
# import pandas as pd
import xarray as xr
import gamstransfer as gt
# import subprocess
import geopandas as gpd
# from shapely.geometry import Polygon, box
from src.funs import distance_2d, sliced_location_optimization, locations_to_gdf

import matplotlib.pyplot as plt

# %%
ROOTDIR = Path('c:/git_repos/impax')

gams_dict = {
    'gams_model': ROOTDIR / 'opt/location_selection.gms',
    'gdx_input': ROOTDIR / 'opt/input_data.gdx',
    'gdx_output': ROOTDIR / 'opt',
    'gams_exe': Path('c:/myprogs/gams/37')
}

# %% read data
# read state borders
vgd = gpd.read_file(ROOTDIR / 'data/VGD_Oesterreich_gen_50_20211001/VGD_50_generalisiert.shp')
states = vgd[['BL', 'geometry']].dissolve(by='BL')
states.reset_index(inplace=True)

clc = gpd.read_file(ROOTDIR / 'data/CLC_2018_AT_clip/CLC18_AT_clip.shp')
clc['CODE_18'] = clc['CODE_18'].astype('int')
clc = clc[clc['CODE_18'] <= 121]
clc = clc.to_crs(states.crs)
clc = clc.buffer(500)

noe = gpd.read_file(ROOTDIR / 'data/RRU_WIND_ZONEN_P19/RRU_WIND_ZONEN_P19Polygon.shp')
noe = noe.to_crs(clc.crs)

bgld = gpd.read_file(ROOTDIR / 'data/widmungsflaechen/BGLD_FLAECHENWIDMUNG.shp')
bgld = bgld.loc[bgld['BEZEICH'] == 'Windkraftanlage', 'geometry']
bgld = bgld.to_crs(clc.crs)

stmk = gpd.read_file(ROOTDIR / 'data/SAPRO_Windenergie_zone/SAPRO_Windenergie_zone.shp')
stmk = stmk.loc[stmk['Zone'] == 'Vorrang', 'geometry']
stmk = stmk.to_crs(clc.crs)

# zones = stmk.loc[stmk['Zone'] == 'Vorrang', 'geometry']
# zones = zones.append(noe['geometry'])
# zones = zones.append(bgld.loc[bgld['BEZEICH'] == 'Windkraftanlage', 'geometry'])
# zones = zones.reset_index(drop=True)

lcoe = xr.open_dataarray(ROOTDIR / 'data/results/lcoe_nogridcost.nc', mask_and_scale=True)
lcoe = lcoe.min(dim='turbine_models')
lcoe = lcoe.rio.reproject(clc.crs)
clipped = lcoe.rio.clip(clc.geometry, clc.crs, drop=False, invert=True)
clipped = clipped.where(clipped != clipped._FillValue)

# clip_all = clipped.rio.clip(zones.geometry, zones.crs, drop=True, invert=False)
noe_clip = clipped.rio.clip(noe.geometry, noe.crs, drop=True, invert=False, all_touched=True)
noe_clip = noe_clip.where(noe_clip != noe_clip._FillValue)
bgld_clip = clipped.rio.clip(bgld.geometry, bgld.crs, drop=True, invert=False, all_touched=True)
bgld_clip = bgld_clip.where(bgld_clip != bgld_clip._FillValue)
stmk_clip = clipped.rio.clip(stmk.geometry, stmk.crs, drop=True, invert=False, all_touched=True)
stmk_clip = stmk_clip.where(stmk_clip != stmk_clip._FillValue)

# %% Optimize turbine locations in zoning areas
cont = gt.Container()

# Lower Austria
loca_noe = sliced_location_optimization(gams_dict, cont, noe_clip, num_slices=1, space_px=2, num_turbines=4930,
                                        gdx_out_string='zones_noe', read_only=False)
lcoe_noe_zone = locations_to_gdf(noe_clip, loca_noe)

# Burgenland
loca_bgld = sliced_location_optimization(gams_dict, cont, bgld_clip, num_slices=1, space_px=2, num_turbines=925,
                                         gdx_out_string='zones_bgld', read_only=False)
lcoe_bgld_zone = locations_to_gdf(bgld_clip, loca_bgld)

# Styria
loca_stmk = sliced_location_optimization(gams_dict, cont, stmk_clip, num_slices=1, space_px=2, num_turbines=820,
                                         gdx_out_string='zones_stmk', read_only=False)
lcoe_stmk_zone = locations_to_gdf(stmk_clip, loca_stmk)

# %% optimize LCOE for any location in Lower Austria
noe_any_clip = clipped.rio.clip(states[states.BL == 'Niederösterreich'].geometry, states.crs, drop=True, invert=False)
noe_any_clip = noe_any_clip.where(noe_any_clip != noe_any_clip._FillValue)
loca_noe_any = sliced_location_optimization(gams_dict, cont, noe_any_clip, num_slices=1, space_px=2, num_turbines=4930,
                                            gdx_out_string='any_noe', read_only=False)
lcoe_noe_any = locations_to_gdf(noe_any_clip, loca_noe_any)

bgld_any_clip = clipped.rio.clip(states[states.BL == 'Burgenland'].geometry, states.crs, drop=True, invert=False)
bgld_any_clip = bgld_any_clip.where(bgld_any_clip != bgld_any_clip._FillValue)
loca_bgld_any = sliced_location_optimization(gams_dict, cont, bgld_any_clip, num_slices=1, space_px=2,
                                             num_turbines=925, gdx_out_string='any_bgld', read_only=False)
lcoe_bgld_any = locations_to_gdf(bgld_any_clip, loca_bgld_any)

stmk_any_clip = clipped.rio.clip(states[states.BL == 'Steiermark'].geometry, states.crs, drop=True, invert=False)
stmk_any_clip = stmk_any_clip.where(stmk_any_clip != stmk_any_clip._FillValue)
loca_stmk_any = sliced_location_optimization(gams_dict, cont, stmk_any_clip, num_slices=1, space_px=2,
                                             num_turbines=820, gdx_out_string='any_stmk', read_only=False)
lcoe_stmk_any = locations_to_gdf(stmk_any_clip, loca_stmk_any)

# %% plot LCOE in zones versus LCOE in all of Lower Austria
fig, ax = plt.subplots(1, 1)
lcoe_noe_zone['LCOE'].plot(ax=ax, color='blue', label='Zones')
lcoe_noe_any['LCOE'].plot(ax=ax, color='green', label='Unrestricted')
ax.set_ylim([18, 60])
ax.set_ylabel('LCOE [€/MWh]')
ax.set_xlabel('Wind turbine locations')
plt.title('Lower Austria')
plt.legend()
plt.grid()
plt.savefig(ROOTDIR / 'figures/NOe_OC_zoning_nogridcost.pdf')
# plt.show()

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
