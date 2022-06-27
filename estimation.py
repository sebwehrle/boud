# %% imports
# from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import pandas as pd
import xarray as xr
import rioxarray as rxr
import statsmodels.formula.api as smf
from src.funs import array_clip, concat_to_pandas, segments
from config import ROOTDIR, country
from scripts.conservation_areas import protected_areas

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

touch = False
BL = 'Niederösterreich'

# %% functions


def clip_raster2shapefile(rasterarray, clipshape, dummyshape=None, crs=None, name=None, all_touched=False):
    """
    Clips an xarray DataArray to a geopandas GeoDataFrame with Polygons. If dummyshape is a GeoDataFrame with Polygons,
    raster cells inside the polygons are set to 1 while raster cells outside are set to 0.
    :param rasterarray: an xarray DataArray
    :param clipshape: a GeoDataFrame with Polygon-geometries to which the rasterarray is clipped
    :param dummyshape: a GeoDataFrame with Polygon geometries. Raster cells inside these Polygons are set to 1
    :param crs: a coordinate reference system
    :param all_touched: option from rioxarray clip()-function. If all_touched is True, all raster cells touched by
    Polygon are affected. Otherwise, only raster cells where center point is inside GeoDataFrame-polygons
    :return: an xarray DataArray
    """
    if crs is None:
        crs = clipshape.crs
    else:
        clipshape = clipshape.to_crs(crs)

    rasterarray = rasterarray.rio.reproject(crs)

    if dummyshape is not None:
        dummyshape = dummyshape.to_crs(crs)
        # for dummy, set all values in rastertemplate to 0
        rasterarray.data[~np.isnan(rasterarray.data)] = 0
        # for dummy, set all raster cells in shapefile to 1
        rasterarray = rasterarray.where(rasterarray.rio.clip(dummyshape.geometry.values, crs, drop=False,
                                                             all_touched=all_touched), 1)
    # clip raster to clipshape
    rasterclip = rasterarray.rio.clip(clipshape.geometry.values, crs, drop=True, all_touched=all_touched)
    rasterclip = rasterclip.squeeze()
    if name is not None:
        rasterclip.name = name
    return rasterclip


# %% read data
vgd = gpd.read_file(ROOTDIR / 'data/vgd/vgd_oesterreich.shp')
states = vgd[['BL', 'geometry']].dissolve(by='BL')
states.reset_index(inplace=True)

zone_noe = gpd.read_file(ROOTDIR / 'data/zones/Zonierung_noe.shp')
zone_noe = zone_noe.to_crs(states.crs)

zone_bgld = gpd.read_file(ROOTDIR / 'data/zones/Widmungsflaechen_bgld.shp')
zone_bgld = zone_bgld.loc[zone_bgld['BEZEICH'] == 'Windkraftanlage', 'geometry']
zone_bgld = zone_bgld.to_crs(states.crs)

stmk = gpd.read_file(ROOTDIR / 'data/zones/Zonierung_stmk.shp')
stmk = stmk.loc[stmk['Zone'] == 'Vorrang', 'geometry']
stmk = stmk.to_crs(states.crs)

cf = xr.open_dataarray(ROOTDIR / f'data/preprocessed/capacity_factors_{country}.nc')
cf = cf.rio.reproject(states.crs)

cf_noe = cf.rio.clip(states.loc[states['BL'] == BL, :].geometry.values, states.crs)
cf_noe = cf_noe.squeeze()
cf_noe.name = 'capacity_factor'

lcoe = xr.open_dataarray(ROOTDIR / f'data/results/lcoe_hoeltinger_{country}.nc')
lcoe = lcoe.rio.reproject(states.crs)
lcoe = lcoe.interp_like(cf)
lcoe_noe = lcoe.rio.clip(states.loc[states['BL'] == BL, :].geometry.values, states.crs)
lcoe_noe = lcoe_noe.squeeze()
lcoe_noe.name = 'lcoe'

dzn_noe = cf_noe.copy()
dzn_noe.data[~np.isnan(dzn_noe.data)] = 0
dzn_noe = dzn_noe.where(dzn_noe.rio.clip(zone_noe.geometry.values, zone_noe.crs, drop=False), 1)
dzn_noe.name = 'zoning'

gd = xr.open_dataarray(ROOTDIR / f'data/preprocessed/grid_distance_{country}.nc', decode_coords='all')
gd = gd.rio.reproject(states.crs)
gd = gd.interp_like(cf)
gd_noe = gd.rio.clip(states.loc[states['BL'] == BL, :].geometry.values, states.crs)
gd_noe = gd_noe.squeeze()
gd_noe.name = 'grid_dist'

# settle / distance to settle

# nature conservation
protected_list = []
for cat, gdf in protected_areas.items():
    protected_array = clip_raster2shapefile(cf, states.loc[states['BL'] == BL, :], dummyshape=gdf,
                                            crs=states.crs, name=cat, all_touched=touch)
    protected_list.append(protected_array)

prota = gpd.GeoDataFrame()
for type, area in protected_areas.items():
    prota = pd.concat([prota, area], axis=0)
prota = prota.dissolve()
prota_array = clip_raster2shapefile(cf, states.loc[states['BL'] == BL, :], dummyshape=prota,
                                            crs=states.crs, name=cat, all_touched=True)

# %% settlement areas
clc = gpd.read_file(ROOTDIR / 'data/clc/CLC_2018_AT.shp')
clc['CODE_18'] = clc['CODE_18'].astype('int')
settle = clc[clc['CODE_18'] <= 121]
settlement = settle.dissolve()
settlement = settlement.buffer(1200)

stl = clip_raster2shapefile(cf, states.loc[states['BL'] == BL, :], dummyshape=settlement,
                            crs=states.crs, name='settlements', all_touched=touch)

airports = clc[clc['CODE_18'] == 124]
airports = airports.buffer(7000)

# %% roads
roads = gpd.read_file(ROOTDIR / 'data/gip/hrng_streets.shp')
roads = roads.dissolve()
roads = clip_raster2shapefile(cf, states.loc[states['BL'] == BL, :], dummyshape=roads, crs=states.crs,
                            name='roads', all_touched=True)

# %% water bodies
water_running = gpd.read_file(ROOTDIR / 'data/water_bodies/main_running_waters.shp')
water_standing = gpd.read_file(ROOTDIR / 'data/water_bodies/main_standing_waters.shp')
waters = pd.concat([water_standing, water_running])
waters = waters.dissolve()
waters = clip_raster2shapefile(cf, states.loc[states['BL'] == BL, :], dummyshape=waters, crs=states.crs,
                               name='waters', all_touched=True)

# %% slope
slope = xr.open_dataarray(ROOTDIR / 'data/elevation/slope_31287.nc')
# slope = slope.rio.reproject(states.crs)

slope_noe = slope.rio.clip(states.loc[states['BL'] == BL, :].geometry.values, states.crs)
slope_noe = slope_noe.squeeze()
slope_noe.name = 'slope'

"""
# %% airport
airport = gpd.GeoDataFrame(data=[0], geometry=gpd.points_from_xy([16.56961], [48.11035]), crs='epsg:4326')
airport = airport.to_crs(states.crs)
airport = airport.buffer(9100)
airport = clip_raster2shapefile(cf, states.loc[states['BL'] == BL, :], dummyshape=airport,
                                crs=states.crs, name='airport', all_touched=True)
"""
# %% buildings outside urban areas
gwrgeb = pd.read_csv('D:/git_repos/impax/data/gwr/ADRESSE.csv', sep=';')
geb = gpd.GeoDataFrame()
for crs in gwrgeb.EPSG.unique():
    tmp = gpd.GeoDataFrame(data=gwrgeb.loc[gwrgeb['EPSG'] == crs, :],
                           geometry=gpd.points_from_xy(gwrgeb.loc[gwrgeb['EPSG'] == crs, 'RW'],
                                                       gwrgeb.loc[gwrgeb['EPSG'] == crs, 'HW']), crs=f'epsg:{crs}')
    tmp = tmp.to_crs('epsg:3416')
    geb = pd.concat([geb, tmp])

# %% land use
widmungen = ['Grünland-Campingplätze', 'Grünland-Kleingarten', 'Grünland-land- und forstwirtschaftliche Hofstelle',
             'Grünland-Erhaltenswertes Gebäude']
landuse = gpd.read_file(ROOTDIR / 'data/landuse/RRU_WI_HUELLEPolygon.shp', encoding='utf-8')
greenland = landuse.loc[landuse['WIDMUNG'].str.contains('|'.join(widmungen)), :]
greenland = greenland.to_crs(states.crs)
greenland = greenland.buffer(750)

greenbuild = gpd.read_file(ROOTDIR / 'data/landuse/RRU_WI_GEBPoint.shp', encoding='utf-8')
greenbuild = greenbuild.to_crs(states.crs)
greenbuild = greenbuild.buffer(750)

green = pd.concat([greenland, greenbuild], axis=0)
gruenland = clip_raster2shapefile(cf, states.loc[states['BL'] == BL, :], dummyshape=green,
                                  crs=states.crs, name='gruenland', all_touched=touch)

# %% plot capacity factor and state boundaries
"""
fig, ax = plt.subplots(1, 1, figsize=(8, 4.5))
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.1)
cf.plot(robust=True, ax=ax, cbar_kwargs={'cax': cax, 'label': 'Auslastung'})
states.boundary.plot(ax=ax, color='black', lw=1)
ax.set_axis_off()
ax.set_title('')
ax.set_title('Erwartete jährliche Auslastung einer\n Enercon E101 3.5 MW Windturbine', loc='center')
plt.tight_layout()
plt.annotate('Quelle: Global Wind Atlas 3, eigene Berechnungen', (5, 6), xycoords='figure points')
plt.savefig('c:/users/sebwe/wind_at.png', dpi=150)
"""
"""
wabo
wabo_dist
road
road_dist
slope

buffer around settlements - 1200 m
merge all protected areas
distance to settlements
flugsicherheit - 1000-6000 m
railways
grünland-widmungen - 750 m 
"""

# %% convert to tidy data
prot_areas = protected_list.copy()
full_list = [prota_array, lcoe_noe, cf_noe, dzn_noe, gd_noe, stl, roads, waters, slope_noe, airport, gruenland]
# full_list = prot_areas + [lcoe_noe, cf_noe, dzn_noe, gd_noe, stl, roads, waters, slope_noe]
tidydat = concat_to_pandas(full_list, 3)
tidydat = tidydat.dropna(how='any', axis=0)

# %% run logit / probit
log_reg = smf.logit("zoning ~ capacity_factor + settlements + airports + remote_buildings + roads + waters + protected_areas + bird_areas + slope",
                    data=tidyvars_bundesland).fit()
# "zoning ~ capacity_factor + settlements + Birds + Habitats + Ramsar + V + roads + waters + slope"
log_reg.summary()

# %% do Firt's logit
from src.funs import fit_firth

abc = fit_firth(tidydat['zoning'], tidydat[['capacity_factor', 'settlements', 'Ramsar', 'roads', 'slope', 'airport', 'gruenland']])

# %%
xog = tidydat[['capacity_factor', 'settlements', 'Ramsar', 'roads', 'slope', 'airport', 'gruenland']]
log_pred = log_reg.predict(exog=xog)
log_pred = log_pred.to_xarray()
log_pred = log_pred.sortby('x')

fig, ax = plt.subplots(1, 1, figsize=(6, 4.5))
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.1)
log_pred.plot(robust=False, ax=ax, vmax=0.15, cbar_kwargs={'cax': cax})
# cf.plot(robust=True, ax=ax, cbar_kwargs={'cax': cax, 'label': 'Auslastung'})
###zone_noe.boundary.plot(ax=ax, color='red', lw=0.2)
ax.set_axis_off()
ax.set_title('')
ax.set_title('Actual and predicted Windpower zones', loc='center')
plt.tight_layout()
# plt.annotate('Quelle: eigene Berechnungen', (5, 6), xycoords='figure points')
# plt.show()
plt.savefig('c:/users/sebwe/predzone_noe.png', dpi=200)

# %%

log_reg.params
log_reg.pvalues

# %% convert results summary to LaTeX
ltx = log_reg.summary().as_latex()

