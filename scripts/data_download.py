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

# %% file, directory, url dict
data_dict = {
    'rnj_power_curve_000-smooth.csv': [ROOTDIR / 'data/power_curves', 'https://raw.githubusercontent.com/renewables-ninja/vwf/master/power_curves/Wind%20Turbine%20Power%20Curves%20%7E%205%20(0.01ms%20with%200.00%20w%20smoother).csv'],
    'oep_wind_turbine_library.zip': [ROOTDIR / 'data/power_curves', 'https://openenergy-platform.org/api/v0/schema/supply/tables/wind_turbine_library/rows?form=datapackage'],
    'sam_wind_turbines.csv': [ROOTDIR / 'data/power_curves', 'https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/Wind%20Turbines.csv'],
    'vgd_oesterreich.zip': [ROOTDIR / 'data/vgd', 'https://data.bev.gv.at/download/data_bev_gv_at/verwaltungsgrenzen/shp/20211001/VGD_Oesterreich_gst_20211001.zip'],
    'CLC_2018_AT.zip': [ROOTDIR / 'data/clc', 'https://docs.umweltbundesamt.at/s/beBw8fmwyCMA2ga/download/CLC_2018_AT_clip.zip'],
    'gridkit_europe.zip': [ROOTDIR / 'data/grid', 'https://zenodo.org/record/47317/files/gridkit_euorpe.zip?download=1'],
    'RRU_WIND_ZONEN_P19.zip': [ROOTDIR / 'data/zones', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RRU_WIND_ZONEN_P19&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
    'Widmungsflaechen.zip': [ROOTDIR / 'data/zones', 'https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=WIDMUNGSFLAECHEN.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4'],
    'SAPRO_Windenergie_zone.zip': [ROOTDIR / 'data/zones', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/SAPRO_Windenergie_zone.zip']
}

# %% get data_dict data0
for file, addr in data_dict.items():
    if not os.path.exists(addr[0]):
        os.mkdir(addr[0])
    download_file(addr[1], addr[0] / file)
    if file[-3:] == 'zip':
        with zipfile.ZipFile(addr[0] / file) as zip_ref:
            zip_ref.extractall(addr[0])
