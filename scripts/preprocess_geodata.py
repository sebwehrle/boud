# %% imports
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from xrspatial import proximity
import multiprocessing as mp
import matplotlib.pyplot as plt

from shapely import wkt
from config import ROOTDIR, country
from src.funs import clip_raster2shapefile, concat_to_pandas, outside, splitlines, calculate_distance

from datetime import datetime

# %% settings
BL = 'Steiermark'
touch = False

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

lcoe = xr.open_dataarray(ROOTDIR / f'data/results/lcoe_{country}.nc')
lcoe = lcoe.rio.reproject(austria.crs)
lcoe_austria = lcoe.rio.clip(austria.geometry.values, austria.crs, all_touched=touch)
lcoe_austria = lcoe_austria.squeeze()
lcoe_austria.name = 'lcoe'

gen = xr.open_dataarray(ROOTDIR / f'data/preprocessed/capacity_factors_{country}.nc')
gen = gen.rio.reproject(austria.crs)
gen = gen.interp_like(lcoe)
gen = gen * 8760 * 0.85 * 3.05  # expected annual generation for a 3.05 MW wind turbine
gen_austria = gen.rio.clip(austria.geometry.values, austria.crs, all_touched=touch)
gen_austria = gen_austria.squeeze()
gen_austria.name = 'generation'

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

zoning_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=zoning, crs=austria.crs,
                                       name='zoning', all_touched=touch)
# TODO: ShapeSkipWarning: Invalid or empty shape None at index 635 will not be rasterized. Projections correct? --> Burgenland!
zoning_austria = zoning_austria.interp_like(lcoe_austria)

# %% protected areas
wdpa = combine_shapefiles(ROOTDIR / 'data/schutzgebiete', 'WDPA_WDOECM_Jun2022_Public_AUT_shp-polygons', [1, 2, 3])
protected_areas_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=wdpa, crs=austria.crs,
                                                name='protected_areas', all_touched=touch)
protected_areas_austria = protected_areas_austria.interp_like(lcoe_austria)
# split up protected areas by IUCN categories:
# iucn_cats = ['Ia', 'Ib', 'II', 'III', 'IV', 'V', 'VI']
# wdpa_subcats = ['Birds', 'Habitats', 'Ramsar']
# protection_categories = wdpa_categories(wdpa, iucn_cats, wdpa_subcats)

# %% Important Bird Areas - BirdLife
iba = gpd.read_file(ROOTDIR / 'data/iba/IBA bounbdaries Austria 6 9 2021.shp')
iba_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=iba, crs=austria.crs,
                                    name='bird_areas', all_touched=touch)
iba_austria = iba_austria.interp_like(lcoe_austria)

# %% Corine Land Cover - settlements and airports
clc = gpd.read_file(ROOTDIR / 'data/clc/CLC_2018_AT.shp')
clc['CODE_18'] = clc['CODE_18'].astype('int')
clc = clc.to_crs(austria.crs)

# airports
airports = clc[clc['CODE_18'] == 124]
airports = airports.buffer(buffers['airports'])
airports_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=airports, crs=austria.crs,
                                         name='airports', all_touched=touch)
airports_austria = airports_austria.interp_like(lcoe_austria)
# settlements
settle = clc.loc[clc['CODE_18'] <= 121, :]
settlements = gpd.GeoDataFrame()
for state in austria['BL'].unique():
    settle_inner = gpd.sjoin(settle, austria.loc[austria['BL'] == state, :], predicate='within', how='inner')
    settlements = pd.concat([settlements, settle_inner])

settlements_distance_austria = calculate_distance(lcoe_austria, settlements, crs=austria.crs)
settlements_distance_austria.name = 'd_settlements'

settlements.geometry = settlements.buffer(buffers['settlements'])
settlements_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=settle, crs=austria.crs,
                                            name='settlements', all_touched=touch)
settlements_austria = settlements_austria.interp_like(lcoe_austria)

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
building_count = lcoe_austria.copy()
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
building_count = xr.where(lcoe_austria.isnull(), lcoe_austria, building_count)
building_count.name = 'building_count'
building_count = building_count.rio.write_crs(lcoe_austria.rio.crs)
print(f'Computation took {datetime.now() - startTime}')

building_count = building_count.interp_like(lcoe_austria)

"""
buildings_by_bundesland = gpd.GeoDataFrame()
for state in austria['BL'].unique():
    buildings_within = gpd.sjoin(buildings, austria.loc[austria['BL'] == state, :], predicate='within', how='inner')
    buildings_by_bundesland = pd.concat([buildings_by_bundesland, buildings_within])
del buildings_within, buildings
"""

# %% proximity to building count
prox_buildings_austria = proximity(xr.where(building_count > 0, 1, 0), x='x', y='y')
prox_buildings_austria = xr.where(lcoe_austria.isnull(), np.nan, prox_buildings_austria)
prox_buildings_austria = prox_buildings_austria.rio.write_crs(lcoe_austria.rio.crs)
prox_buildings_austria.name = 'proximity_buildings'

prox_buildings_austria = prox_buildings_austria.interp_like(lcoe_austria)

# %% exclude buildings in settlements
startTime = datetime.now()

with mp.Pool(np.min([9, mp.cpu_count() - 2])) as pool:
    remotes = pool.starmap(outside,
                           [[buildings_by_bundesland, settlements, 'BL', land] for land in austria['BL'].unique()])
buildings_remote = pd.concat(remotes)
del remotes

if buffers['greenland'] is not None:
    buildings_remote.geometry = buildings_remote.buffer(buffers['greenland'])

remote_buildings_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=buildings_remote, crs=austria.crs,
                                                 name='remote_buildings', all_touched=touch)
print(f'Computation took {datetime.now() - startTime}')
remote_buildings_austria = remote_buildings_austria.interp_like(lcoe_austria)

remote_buildings_distance_austria = calculate_distance(lcoe_austria, buildings_remote, crs=austria.crs)
remote_buildings_distance_austria.name = 'd_remote'
remote_buildings_distance_austria = remote_buildings_distance_austria.interp_like(lcoe_austria)

# %% roads
roads = gpd.read_file(ROOTDIR / 'data/gip/hrng_streets.shp')
roads_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=roads, crs=austria.crs,
                                      name='roads', all_touched=touch)
roads_austria = roads_austria.interp_like(lcoe_austria)

roads_distance_austria = calculate_distance(lcoe_austria, roads, crs=austria.crs)
roads_distance_austria.name = 'd_roads'
roads_distance_austria = roads_distance_austria.interp_like(lcoe_austria)

# %% water bodies
waters = pd.concat([gpd.read_file(ROOTDIR / 'data/water_bodies/main_standing_waters.shp'),
                    gpd.read_file(ROOTDIR / 'data/water_bodies/main_running_waters.shp')])
waters_austria = clip_raster2shapefile(lcoe_austria, austria, dummyshape=waters, crs=austria.crs,
                                       name='waters', all_touched=touch)
waters_austria = waters_austria.interp_like(lcoe_austria)

waters_distance_austria = calculate_distance(lcoe_austria, waters, crs=austria.crs)
waters_distance_austria.name = 'd_waters'
waters_distance_austria = waters_distance_austria.interp_like(lcoe_austria)

# %% distance to high-voltage grid
lines = pd.read_csv(ROOTDIR / 'data/grid/gridkit_europe-highvoltage-links.csv')
lines['geometry'] = lines['wkt_srid_4326'].str.replace('SRID=4326;', '')
lines['geometry'] = lines['geometry'].apply(wkt.loads)
lines = gpd.GeoDataFrame(lines, crs='epsg:4326')
lines = lines.to_crs(austria.crs)
lines = gpd.clip(lines, austria)
lines = lines.explode()
lines = splitlines(lines, 64)
lines.crs = austria.crs

dist = calculate_distance(lcoe_austria, lines, crs=austria.crs)
dist = dist.interp_like(lcoe_austria)
dist.name = 'd_grid'


# %% terrain slope
slope = xr.open_dataarray(ROOTDIR / 'data/elevation/slope_31287.nc')
slope = slope.squeeze()
slope = slope.rio.reproject(austria.crs)
slope_austria = slope.rio.clip(austria.geometry.values, austria.crs, all_touched=touch)
slope_austria = slope_austria.interp_like(lcoe_austria)
slope_austria.name = 'slope'
slope_austria = slope_austria.interp_like(lcoe_austria)

# %% tidy vars for all of Austria
var_list = [zoning_austria, lcoe_austria, gen_austria, settlements_austria, settlements_distance_austria,
            airports_austria, building_count, prox_buildings_austria, remote_buildings_austria,
            remote_buildings_distance_austria, roads_austria, roads_distance_austria, waters_austria,
            waters_distance_austria, protected_areas_austria, iba_austria, slope_austria, dist]
tidyvars_austria = concat_to_pandas(var_list, digits=4, drop_labels=['band', 'spatial_ref', 'turbine_models'])
tidyvars_austria = tidyvars_austria.dropna(how='any', axis=0)
tidyvars_austria.to_csv(ROOTDIR / 'data/vars_austria_notouch.csv')

# %% tidy vars for Bundesländer
for BL in zones.keys():
    bundesland = austria.loc[austria['BL'] == BL, :]
    zone_bundesland = zoning_austria.rio.clip(bundesland.geometry, bundesland.crs)
    xatp_bundesland = lcoe_austria.rio.clip(bundesland.geometry, bundesland.crs)
    gen_bundesland = gen_austria.rio.clip(bundesland.geometry, bundesland.crs)
    settlements_bundesland = settlements_austria.rio.clip(bundesland.geometry, bundesland.crs)
    settlements_distance_bundesland = settlements_distance_austria.rio.clip(bundesland.geometry, bundesland.crs)
    airports_bundesland = airports_austria.rio.clip(bundesland.geometry, bundesland.crs)
    building_count_bundesland = building_count.rio.clip(bundesland.geometry, bundesland.crs)
    prox_buildings_bundesland = prox_buildings_austria.rio.clip(bundesland.geometry, bundesland.crs)
    remote_buildings_bundesland = remote_buildings_austria.rio.clip(bundesland.geometry, bundesland.crs)
    remote_buildings_distance_bundesland = remote_buildings_distance_austria.rio.clip(bundesland.geometry, bundesland.crs)
    roads_bundesland = roads_austria.rio.clip(bundesland.geometry, bundesland.crs)
    roads_distance_bundesland = roads_distance_austria.rio.clip(bundesland.geometry, bundesland.crs)
    waters_bundesland = waters_austria.rio.clip(bundesland.geometry, bundesland.crs)
    waters_distance_bundesland = waters_distance_austria.rio.clip(bundesland.geometry, bundesland.crs)
    protected_areas_bundesland = protected_areas_austria.rio.clip(bundesland.geometry, bundesland.crs)
    iba_bundesland = iba_austria.rio.clip(bundesland.geometry, bundesland.crs)
    slope_bundesland = slope_austria.rio.clip(bundesland.geometry, bundesland.crs)

    vars_bundesland = [zone_bundesland, xatp_bundesland, gen_bundesland, settlements_bundesland,
                       settlements_distance_bundesland, airports_bundesland, building_count_bundesland,
                       prox_buildings_bundesland, remote_buildings_bundesland, remote_buildings_distance_bundesland,
                       roads_bundesland, roads_distance_bundesland, waters_bundesland, waters_distance_bundesland,
                       protected_areas_bundesland, iba_bundesland, slope_bundesland]
    tidyvars_bundesland = concat_to_pandas(vars_bundesland, digits=4,
                                           drop_labels=['band', 'spatial_ref', 'turbine_models'])
    tidyvars_bundesland = tidyvars_bundesland.dropna(how='any', axis=0)
    tidyvars_bundesland.to_csv(ROOTDIR / f'data/vars_{BL}_notouch.csv'.replace('ö', 'oe'))

# %% unique attributions
import pandas as pd
import rioxarray
import geopandas as gpd
import matplotlib.pyplot as plt
from config import ROOTDIR
from src.funs import concat_to_pandas

tidyvars_auq = pd.read_csv(ROOTDIR / 'data/vars_austria.csv')
# no remote buildings in settlements
tidyvars_auq.loc[tidyvars_auq['settlements'] == 1, 'remote_buildings'] = 0
# distance to settlement = 0 in settlements
tidyvars_auq.loc[tidyvars_auq['settlements'] == 1, 'd_settlements'] = 0
# no roads in settlements
tidyvars_auq.loc[tidyvars_auq['settlements'] == 1, 'roads'] = 0
# no important bird areas in protected areas
tidyvars_auq.loc[tidyvars_auq['protected_areas'] == 1, 'bird_areas'] = 0
# distance to remote buildings = 0 in remote_buildings
tidyvars_auq.loc[tidyvars_auq['remote_buildings'] == 1, 'd_remote'] = 0
# distance to waters = 0 in waters
tidyvars_auq.loc[tidyvars_auq['waters'] == 1, 'd_waters'] = 0

# write to disk
tidyvars_auq.to_csv(ROOTDIR / 'data/vars_austria_uniqued.csv')

# %% unique tidyvars for bundesländer
austria = gpd.read_file(ROOTDIR / 'data/vgd/vgd_oesterreich.shp')
austria = austria[['BL', 'geometry']].dissolve(by='BL')
austria.reset_index(inplace=True)

tidyvars_auq.index = pd.MultiIndex.from_arrays([tidyvars_auq['y'], tidyvars_auq['x']])
tidyvars_auq = tidyvars_auq.drop(['x', 'y'], axis=1)
tidyxar_auq = tidyvars_auq.to_xarray()
tidyxar_auq = tidyxar_auq.rio.write_crs(austria.crs)

BL = 'Niederösterreich'
bundesland = austria.loc[austria['BL'] == BL, :]
vars_bundesland = [datavar[1].rio.clip(bundesland.geometry, bundesland.crs) for datavar in tidyxar_auq.data_vars.items()]
vars_bundesland = concat_to_pandas(vars_bundesland, digits=4, drop_labels=['spatial_ref'])

vars_bundesland.to_csv(ROOTDIR / f'data/vars_{BL}_uniqued.csv'.replace('ö', 'oe'))
