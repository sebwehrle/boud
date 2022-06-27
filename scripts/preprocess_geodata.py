# %% imports
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import multiprocessing as mp
import matplotlib.pyplot as plt

from config import ROOTDIR, country
from src.funs import clip_raster2shapefile, concat_to_pandas, outside
from scripts.distances import calculate_distance

from datetime import datetime

# %% settings
BL = 'Steiermark'
touch = True

zones = {
    'Niederösterreich': ROOTDIR / 'data/zones/Zonierung_noe.shp',
    'Burgenland': ROOTDIR / 'data/zones/Widmungsflaechen_bgld.shp',
    'Steiermark': ROOTDIR / 'data/zones/Zonierung_stmk.shp',
}

buffers = {
    'airports': 7000,
    'settlements': 1000,
    'greenland': None,
}

# %% functions
def wdpa_categories(wdpa, iucn_cats, wdpa_subcats):
    segments = {}
    for seg in iucn_cats:
        tmp = wdpa.loc[wdpa['IUCN_CAT'] == seg]
        tmp = tmp.dissolve(by='IUCN_CAT')
        segs = {
            seg: tmp
        }
        segments.update(segs)
    for seg in wdpa_subcats:
        tmp = wdpa.loc[wdpa['DESIG_ENG'].str.contains(seg)]
        tmp = tmp.dissolve(by='DESIG_ENG')
        subsegs = {
            seg: tmp
        }
        segments.update(subsegs)
    return segments


def combine_shapefiles(directory, fname, iterator):
    gdf = gpd.GeoDataFrame()
    for i in iterator:
        shp = gpd.read_file(directory / f'{fname}_{i}.shp')
        gdf = pd.concat([gdf, shp], axis=0, join='outer')
    return gdf


# %% read data
austria = gpd.read_file(ROOTDIR / 'data/vgd/vgd_oesterreich.shp')
austria = austria[['BL', 'geometry']].dissolve(by='BL')
austria.reset_index(inplace=True)

xatp = xr.open_dataarray(ROOTDIR / f'data/results/lcoe_{country}.nc')
xatp = xatp.rio.reproject(austria.crs)

xatp_austria = xatp.rio.clip(austria.geometry.values, austria.crs)
xatp_austria = xatp_austria.squeeze()
xatp_austria.name = 'lcoe'

# %% wind power zoning
zoning = []
for BL in zones.keys():
    zone = gpd.read_file(zones[BL])
    if BL == 'Burgenland':
        zone = zone.loc[zone['BEZEICH'] == 'Windkraftanlage', 'geometry']
    elif BL == 'Steiermark':
        zone = zone.loc[zone['Zone'] == 'Vorrang', 'geometry']
    zone = zone.to_crs(austria.crs)
    zoning.append(zone)
zoning = pd.concat(zoning)
zoning.reset_index(inplace=True)

zoning_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=zoning, crs=austria.crs,
                                       name='zoning', all_touched=touch)
# TODO: ShapeSkipWarning: Invalid or empty shape None at index 635 will not be rasterized. Projections correct? --> Burgenland!
# zone_bundesland = xatp_austria.copy()
# zone_bundesland.data[~np.isnan(zone_bundesland.data)] = 0
# zone_bundesland = zone_bundesland.where(zone_bundesland.rio.clip(zone.geometry.values, zone.crs, drop=False), 1)
# zone_bundesland.name = 'zoning'

# %% protected areas
wdpa = combine_shapefiles(ROOTDIR / 'data/schutzgebiete', 'WDPA_WDOECM_Jun2022_Public_AUT_shp-polygons', [1, 2, 3])
protected_areas_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=wdpa, crs=austria.crs,
                                                name='protected_areas', all_touched=touch)

# split up protected areas by IUCN categories:
# iucn_cats = ['Ia', 'Ib', 'II', 'III', 'IV', 'V', 'VI']
# wdpa_subcats = ['Birds', 'Habitats', 'Ramsar']
# protection_categories = wdpa_categories(wdpa, iucn_cats, wdpa_subcats)

# %% Important Bird Areas - BirdLife
iba = gpd.read_file(ROOTDIR / 'data/iba/IBA bounbdaries Austria 6 9 2021.shp')
iba_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=iba, crs=austria.crs,
                                    name='bird_areas', all_touched=touch)


# %% Corine Land Cover - settlements and airports
clc = gpd.read_file(ROOTDIR / 'data/clc/CLC_2018_AT.shp')
clc['CODE_18'] = clc['CODE_18'].astype('int')
clc = clc.to_crs(austria.crs)

# airports
airports = clc[clc['CODE_18'] == 124]
airports = airports.buffer(buffers['airports'])
airports_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=airports, crs=austria.crs,
                                         name='airports', all_touched=touch)

# settlements
settle = clc.loc[clc['CODE_18'] <= 121, :]
settlements = gpd.GeoDataFrame()
for state in austria['BL'].unique():
    settle_inner = gpd.sjoin(settle, austria.loc[austria['BL'] == state, :], predicate='within', how='inner')
    settlements = pd.concat([settlements, settle_inner])

settlements.geometry = settlements.buffer(buffers['settlements'])
settlements_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=settle, crs=austria.crs,
                                            name='settlements', all_touched=touch)

# %% remote buildings
gwr = pd.read_csv(ROOTDIR / 'data/gwr/ADRESSE.csv', sep=';')

# transform to GeoDataFrame with single projection
buildings = [gpd.GeoDataFrame(
    geometry=gpd.points_from_xy(gwr.loc[gwr.EPSG == projection, 'RW'],
                                gwr.loc[gwr.EPSG == projection, 'HW']), crs=f'epsg:{projection}').to_crs(austria.crs)
             for projection in gwr.EPSG.unique()]
buildings = pd.concat(buildings)
buildings.reset_index(inplace=True)

#  add Bundesland-column
buildings_by_bundesland = [gpd.sjoin(buildings, austria.loc[austria['BL'] == state, :], predicate='within', how='inner')
                           for state in austria['BL'].unique()]
buildings_by_bundesland = pd.concat(buildings_by_bundesland)
buildings_by_bundesland.reset_index(inplace=True)

# %% count buildings per grid cell
startTime = datetime.now()

# bds is a 1-D data array of x- and y-values
bds = pd.DataFrame(data={'x': buildings.loc[:, 'geometry'].x, 'y': buildings.loc[:, 'geometry'].y})
bds = bds.to_xarray()
# prepare 2-D data array-template with coordinates as data
building_count = xatp_austria.copy()
building_count.name = 'building_count'
building_count = building_count.stack(z=('x', 'y'))
building_count.data = building_count.z.data
building_count = building_count.unstack()
# peter's method 1
num_buildings = building_count.sel(x=bds.x, y=bds.y, method='nearest')
num_buildings = num_buildings.groupby(num_buildings).count()
# recycle 2-D template and assign building count to raster cells
building_count.data = xr.zeros_like(building_count)
building_count = building_count.stack(z=('x', 'y'))
building_count.loc[dict(z=num_buildings.building_count)] = num_buildings.data
building_count = building_count.unstack()
building_count.data = building_count.data.astype(float)
building_count = xr.where(xatp_austria.isnull(), xatp_austria, building_count)
building_count.name = 'building_count'
building_count = building_count.rio.write_crs(xatp_austria.rio.crs)
print(f'Computation took {datetime.now() - startTime}')

"""
buildings_by_bundesland = gpd.GeoDataFrame()
for state in austria['BL'].unique():
    buildings_within = gpd.sjoin(buildings, austria.loc[austria['BL'] == state, :], predicate='within', how='inner')
    buildings_by_bundesland = pd.concat([buildings_by_bundesland, buildings_within])
del buildings_within, buildings
"""

# %% exclude buildings in settlements
startTime = datetime.now()

with mp.Pool(np.min([9, mp.cpu_count() - 2])) as pool:
    remotes = pool.starmap(outside, [[buildings_by_bundesland, settlements, 'BL', land] for land in austria['BL'].unique()])
buildings_remote = pd.concat(remotes)
del remotes

# TODO: Broken with "austria"
if buffers['greenland'] is not None:
    buildings_remote.geometry = buildings_remote.buffer(buffers['greenland'])

remote_buildings_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=buildings_remote, crs=austria.crs,
                                                 name='remote_buildings', all_touched=touch)
print(f'Computation took {datetime.now() - startTime}')

# %% roads
roads = gpd.read_file(ROOTDIR / 'data/gip/hrng_streets.shp')
roads_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=roads, crs=austria.crs,
                                      name='roads', all_touched=touch)

# %% water bodies
waters = pd.concat([gpd.read_file(ROOTDIR / 'data/water_bodies/main_standing_waters.shp'),
                    gpd.read_file(ROOTDIR / 'data/water_bodies/main_running_waters.shp')])
waters_austria = clip_raster2shapefile(xatp_austria, austria, dummyshape=waters, crs=austria.crs,
                                       name='waters', all_touched=touch)

# %% terrain slope
slope = xr.open_dataarray(ROOTDIR / 'data/elevation/slope_31287.nc')
slope = slope.squeeze()
slope = slope.rio.reproject(austria.crs)
slope_austria = slope.rio.clip(austria.geometry.values, austria.crs)
slope_austria = slope_austria.interp_like(xatp_austria)
slope_austria.name = 'slope'

# %% tidy vars for all of Austria
var_list = [zoning_austria, xatp_austria, settlements_austria, airports_austria, building_count,
            remote_buildings_austria, roads_austria, waters_austria, protected_areas_austria, iba_austria,
            slope_austria]
tidyvars_austria = concat_to_pandas(var_list, digits=4)
tidyvars_austria = tidyvars_austria.dropna(how='any', axis=0)
tidyvars_austria.to_csv(ROOTDIR / 'data/vars_austria.csv')

# %% tidy vars for Bundesländer
for BL in zones.keys():
    bundesland = austria.loc[austria['BL'] == BL, :]
    zone_bundesland = zoning_austria.rio.clip(bundesland.geometry, bundesland.crs)
    xatp_bundesland = xatp_austria.rio.clip(bundesland.geometry, bundesland.crs)
    settlements_bundesland = settlements_austria.rio.clip(bundesland.geometry, bundesland.crs)
    airports_bundesland = airports_austria.rio.clip(bundesland.geometry, bundesland.crs)
    building_count_bundesland = building_count.rio.clip(bundesland.geometry, bundesland.crs)
    remote_buildings_bundesland =remote_buildings_austria.rio.clip(bundesland.geometry, bundesland.crs)
    roads_bundesland = roads_austria.rio.clip(bundesland.geometry, bundesland.crs)
    waters_bundesland = waters_austria.rio.clip(bundesland.geometry, bundesland.crs)
    protected_areas_bundesland = protected_areas_austria.rio.clip(bundesland.geometry, bundesland.crs)
    iba_bundesland = iba_austria.rio.clip(bundesland.geometry, bundesland.crs)
    slope_bundesland = slope_austria.rio.clip(bundesland.geometry, bundesland.crs)

    vars_bundesland = [zone_bundesland, xatp_bundesland, settlements_bundesland, airports_bundesland,
                       building_count_bundesland, remote_buildings_bundesland, roads_bundesland, waters_bundesland,
                       protected_areas_bundesland, iba_bundesland, slope_bundesland]
    tidyvars_bundesland = concat_to_pandas(vars_bundesland, digits=4)
    tidyvars_bundesland = tidyvars_bundesland.dropna(how='any', axis=0)
# TODO: Replace Umlauts in filename
    tidyvars_bundesland.to_csv(ROOTDIR / f'data/vars_{BL}.csv')

# unique attribution of buildings
# tidyvars.loc[tidyvars['settlements'] == 1, 'remote_buildings'] = 0
# unique attribute of roads - overland/non-urban-roads only
# tidyvars.loc[tidyvars['settlements'] == 1, 'roads'] = 0

# settlements, airports,
