# %% imports
import pandas as pd
import geopandas as gpd
import xarray as xr
import rioxarray as rxr
from shapely import wkt

from config import ROOTDIR, country
from src.funs import segments, splitlines, kdnearest, calculate_distance

# %% read data
# open file which will hold the distance data
template = xr.open_rasterio(ROOTDIR / f'data/gwa3/{country}_combined-Weibull-A_100.tif')
template = template.rio.reproject('EPSG:3416').squeeze()
# template_stacked = template.stack(xy=['x', 'y'])

austria = gpd.read_file(ROOTDIR / 'data/vgd/vgd_oesterreich.shp')
austria = austria.dissolve(by='ST')
austria = austria.to_crs(template.rio.crs)

lines = pd.read_csv(ROOTDIR / 'data/grid/gridkit_europe-highvoltage-links.csv')
lines['geometry'] = lines['wkt_srid_4326'].str.replace('SRID=4326;', '')
lines['geometry'] = lines['geometry'].apply(wkt.loads)
lines = gpd.GeoDataFrame(lines, crs='epsg:4326')
lines = lines.to_crs(template.rio.crs)
lines = gpd.clip(lines, austria)
lines = lines.explode()

# split lines
lines = splitlines(lines, 64)

clc = gpd.read_file(ROOTDIR / 'data/clc/CLC_2018_AT.shp')
clc.crs = 'epsg:3035'
clc.to_crs('epsg:3416')
clc['CODE_18'] = clc['CODE_18'].astype('int')
settle = clc[clc['CODE_18'] <= 121]
settlement = settle.boundary.explode()
settlement = settlement.reset_index(drop=True)
settlement = gpd.GeoDataFrame(geometry=segments(settlement))
infra = lines.append(settlement)
infra.crs = 'epsg:3416'

# %%
"""
# create GeoDataFrame with a line for each coordinate in template file
gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(
    template_stacked[template_stacked.notnull()].indexes['xy'].get_level_values(0),
    template_stacked[template_stacked.notnull()].indexes['xy'].get_level_values(1), crs='epsg:3416'))
gdf = gdf.to_crs('epsg:3416')

dists = kdnearest(gdf, infra, gdfB_cols=[])  # gdfB_cols=['name', 'v_id_1', 'v_id_2'])
"""
dists = calculate_distance(template, infra)


# %% assign values back to DataArray
dists.index = pd.MultiIndex.from_arrays([dists['geometry'].y, dists['geometry'].x])
dists = dists['dist']
dst = dists.to_xarray()
dst = dst.rio.write_crs(gdf.crs)

# muss ich hier den umweg über df gehen? warum nicht direkt template_stacked.values = dists.values?
mix = template_stacked.coords.indexes['xy']
mix = pd.MultiIndex.from_arrays([mix.get_level_values(0).values.round(digits),
                                 mix.get_level_values(1).values.round(digits)])
df = pd.DataFrame(0, mix, ['dist'])
df['dist'] = dists['dist']
template_stacked.values = df['dist'].values
cfu = template_stacked.unstack().transpose()
cfu = cfu.rio.write_crs(template.rio.crs)

# %% assign values back to DataArray
# set multiindex to GeoDataFrame
gmx = pd.MultiIndex.from_arrays([dists['geometry'].x.round(8), dists['geometry'].y.round(8)])
dists.index = gmx

mix = cf_stacked.coords.indexes['xy']
mix = pd.MultiIndex.from_arrays([mix.get_level_values(0).values.round(8), mix.get_level_values(1).values.round(8)])
df = pd.DataFrame(0, mix, ['dist'])
df['dist'] = dists['dist']
cf_stacked.values = df['dist'].values
cfu = cf_stacked.unstack().transpose()

cfu.to_netcdf(path=ROOTDIR / 'data/grid_distance.nc')


 # %% write results
cfu.to_netcdf(path=ROOTDIR / f'data/preprocessed/grid_distance_{country}.nc')
