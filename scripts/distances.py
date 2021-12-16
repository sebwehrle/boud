# %% imports
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
from shapely import wkt

from config import where
from src.funs import segments, splitlines, kdnearest

# %% read data
if where == 'home':
    ROOTDIR = Path('/')
else:
    ROOTDIR = Path('d:/git_repos/impax')

# open file which will hold the distance data
template = rxr.open_rasterio(ROOTDIR / 'data/windatlas/a120_100m_Lambert.img')
template.values[template.values <= 0] = np.nan
template = template.rio.reproject('EPSG:3416').squeeze()
template_stacked = template.stack(xy=['x', 'y'])

austria = gpd.read_file(ROOTDIR / 'data/Staatsgrenze/Staatsgebiet_50.shp')

lines = pd.read_csv(ROOTDIR / 'data/gridkit_europe/gridkit_europe-highvoltage-links.csv')
lines['geometry'] = lines['wkt_srid_4326'].str.replace('SRID=4326;', '')
lines['geometry'] = lines['geometry'].apply(wkt.loads)
lines = gpd.GeoDataFrame(lines, crs='epsg:4326')
lines = gpd.clip(lines, austria)
lines = lines.explode()
lines = lines.to_crs('epsg:3416')

# split lines
lines = splitlines(lines, 64)

clc = gpd.read_file(ROOTDIR / 'data/CLC_2018_AT_clip/CLC18_AT_clip.shp')
clc['CODE_18'] = clc['CODE_18'].astype('int')
settle = clc[clc['CODE_18'] <= 121]
settlement = settle.boundary.explode()
settlement = settlement.reset_index(drop=True)

settlement = gpd.GeoDataFrame(geometry=segments(settlement))
infra = lines.append(settlement)

# %% calculate distances
# create GeoDataFrame with a line for each coordinate in template file
gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(
    template_stacked[template_stacked.notnull()].indexes['xy'].get_level_values(0),
    template_stacked[template_stacked.notnull()].indexes['xy'].get_level_values(1), crs='epsg:3416'))
gdf = gdf.to_crs('epsg:3416')

dists = kdnearest(gdf, infra, gdfB_cols=[])  # gdfB_cols=['name', 'v_id_1', 'v_id_2'])
# dists = dists.to_crs('epsg:3416')  # should already be in epsg:3416!

# %% assign values back to DataArray
# set multiindex to GeoDataFrame
digits = 3  # 8
gmx = pd.MultiIndex.from_arrays([dists['geometry'].x.round(digits), dists['geometry'].y.round(digits)])
dists.index = gmx

# muss ich hier den umweg über df gehen? warum nicht direkt template_stacked.values = dists.values?
mix = template_stacked.coords.indexes['xy']
mix = pd.MultiIndex.from_arrays([mix.get_level_values(0).values.round(digits),
                                 mix.get_level_values(1).values.round(digits)])
df = pd.DataFrame(0, mix, ['dist'])
df['dist'] = dists['dist']
template_stacked.values = df['dist'].values
cfu = template_stacked.unstack().transpose()

# %% write results
cfu.to_netcdf(path=ROOTDIR / 'data/preprocessed/grid_distance.nc')