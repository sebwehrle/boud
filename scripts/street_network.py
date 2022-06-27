# %% imports
import os
import subprocess
import zipfile
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from config import ROOTDIR

# %% process GIP geopackage
# 'https://open.gip.gv.at/ogd/B_gip_network_ogd.zip'  # GIP Network: Basisnetz
gip_directory = ROOTDIR / 'data/gip/'
gip_file = 'C:/git_repos/impax/data/gip/B_gip_network_ogd.zip'
# unzip
with zipfile.ZipFile(gip_file) as zip_ref:
    zip_ref.extractall(gip_directory)

# convert to shapefiles
os.chdir(gip_directory)
subprocess.run("""ogr2ogr -f "ESRI shapefile" shp gip_network_ogd.gpkg""")

# remove unnecessary shapefiles


# %% read data
gip_shp = ROOTDIR / 'data/gip/shp/EDGE_OGD.shp'
hochrangig = ['A', 'S', 'B', 'L']
hrng = gpd.GeoDataFrame()

# total number of rows: 1 532 485
for n in range(1, 63):
    gip = gpd.read_file(gip_shp, rows=slice((n-1)*25000, n*25000))
    gip = gip.loc[gip['EDGECAT'].isin(hochrangig)]
    hrng = pd.concat([hrng, gip])
    gip = []

hrng.to_file(ROOTDIR / 'data/gip/hrng_streets.shp')

# %% process water bodies
# 'https://docs.umweltbundesamt.at/s/YkgTDiDs9DPstCJ/download/Routen_v16.zip'  # Fließgewässer
# 'https://docs.umweltbundesamt.at/s/t4jHoXmrwrsjnea/download/stehendeGewaesser_v16.zip'  # stehende Gewässer
main_water_bodies = ['100 km² Gewässer', '1000 km² Gewässer', '10000 km² Gewässer', '500 km² Gewässer', '4000 km² Gewässer']
wbd = gpd.read_file(ROOTDIR / 'data/water_bodies/Fliessgewaesser.shp')
wbd = wbd.loc[wbd['GEW_KAT'].isin(main_water_bodies)]
wbd = wbd.dissolve()
wbd.to_file(ROOTDIR / 'data/water_bodies/main_running_waters.shp')

lks = gpd.read_file(ROOTDIR / 'data/water_bodies/stehendeGewaesser.shp')
lks = lks.loc[lks['FLAECHEKM2'] >= 0.03125, :]
lks.to_file(ROOTDIR / 'data/water_bodies/main_standing_waters.shp')
