# %% imports
import os
import requests
import zipfile

from config import ROOTDIR

# %% define functions


def download_file(url, filename):
    with requests.get(url) as r:
        with open(filename, 'wb') as f:
            f.write(r.content)


# %% get global wind atlas
country = ['AUT']
layer = ['air-density', 'combined-Weibull-A', 'combined-Weibull-k']
ground = ['elevation_w_bathymetry']
height = ['50', '100', '150']

if not os.path.exists(ROOTDIR / 'data/gwa3'):
    os.mkdir(ROOTDIR / 'data/gwa3')

url_gwa = 'https://globalwindatlas.info/api/gis/country'
for c in country:
    for l in layer:
        for h in height:
            fname = f'{c}_{l}_{h}.tif'
            download_file(f'{url_gwa}/{c}/{l}/{h}', ROOTDIR / 'data/gwa3' / fname)
    for g in ground:
        fname = f'{c}_{g}.tif'
        download_file(f'{url_gwa}/{c}/{g}', ROOTDIR / 'data/gwa3' / fname)

# %% get powercurves from rnj and https://openenergy-platform.org/dataedit/view/supply/wind_turbine_library
dir_tpc = ROOTDIR / 'data/power_curves'
url_rnj = 'https://raw.githubusercontent.com/renewables-ninja/vwf/master/power_curves/Wind%20Turbine%20Power%20Curves%20%7E%205%20(0.01ms%20with%200.00%20w%20smoother).csv'
url_oep = 'https://openenergy-platform.org/api/v0/schema/supply/tables/wind_turbine_library/rows?form=datapackage'
url_sam = 'https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/Wind%20Turbines.csv'
fname_rnj = 'rnj_power_curve_000-smooth.csv'
fname_oep = 'oep_wind_turbine_library.zip'
fname_sam = 'sam_wind_turbines.csv'

if not os.path.exists(dir_tpc):
    os.mkdir(dir_tpc)

download_file(url_rnj, dir_tpc / fname_rnj)

download_file(url_oep, dir_tpc / fname_oep)
with zipfile.ZipFile(dir_tpc / fname_oep) as zip_ref:
    zip_ref.extractall(dir_tpc)

download_file(url_sam, dir_tpc / fname_sam)

# %% get borders
dir_vgd = ROOTDIR / 'data/vgd'
url_vgd = 'https://data.bev.gv.at/download/data_bev_gv_at/verwaltungsgrenzen/shp/20211001/VGD_Oesterreich_gst_20211001.zip'
fname = 'vgd_oesterreich.zip'

if not os.path.exists(dir_vgd):
    os.mkdir(dir_vgd)

download_file(url_vgd, dir_vgd / fname)

with zipfile.ZipFile(dir_vgd / fname) as zip_ref:
    zip_ref.extractall(dir_vgd)

# %% get corine land cover
dir_clc = ROOTDIR / 'data/clc'
url_clc = 'https://docs.umweltbundesamt.at/s/beBw8fmwyCMA2ga/download/CLC_2018_AT_clip.zip'
fname = 'CLC_2018_AT.zip'

if not os.path.exists(dir_clc):
    os.mkdir(dir_clc)

download_file(url_clc, dir_clc / fname)

with zipfile.ZipFile(dir_clc / fname) as zip_ref:
    zip_ref.extractall(dir_clc)

# %% get grid data
dir_gke = ROOTDIR / 'data/grid'
url_gke = 'https://zenodo.org/record/47317/files/gridkit_euorpe.zip?download=1'
fname = 'gridkit_europe.zip'

if not os.path.exists(dir_gke):
    os.mkdir(dir_gke)

download_file(url_gke, dir_gke / fname)
with zipfile.ZipFile(dir_gke / fname) as zip_ref:
    zip_ref.extractall(dir_gke)

# %% get wind power zones
dir_zones = ROOTDIR / 'data/zones'
if not os.path.exists(dir_zones):
    os.mkdir(dir_zones)

url_noe = 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RRU_WIND_ZONEN_P19&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'
fname_noe = 'RRU_WIND_ZONEN_P19.zip'

url_bgld = 'https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=WIDMUNGSFLAECHEN.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4'
fname_bgld = 'Widmungsflaechen.zip'

url_stmk = 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/SAPRO_Windenergie_zone.zip'
fname_stmk = 'SAPRO_Windenergie_zone.zip'

download_file(url_noe, dir_zones / fname_noe)
with zipfile.ZipFile(dir_zones / fname_noe) as zip_ref:
    zip_ref.extractall(dir_zones)

download_file(url_bgld, dir_zones / fname_bgld)
with zipfile.ZipFile(dir_zones / fname_bgld) as zip_ref:
    zip_ref.extractall(dir_zones)

download_file(url_stmk, dir_zones / fname_stmk)
with zipfile.ZipFile(dir_zones / fname_stmk) as zip_ref:
    zip_ref.extractall(dir_zones)

