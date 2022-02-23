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
    'SAPRO_Windenergie_zone.zip': [ROOTDIR / 'data/zones', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/SAPRO_Windenergie_zone.zip'],
    'WINDKRAFT_AUSSCHLUSSZONE.zip': [ROOTDIR / 'data/zones', 'https://e-gov.ooe.gv.at/at.gv.ooe.dorisdaten/DORIS_U/WINDKRAFT_AUSSCHLUSSZONE.zip'],
    'nationalparks.zip': [ROOTDIR / 'data/schutzgebiete', 'https://docs.umweltbundesamt.at/s/Ezq6NEJ8LTg6s8j/download/nationalparks_2012.zip'],
    'natura_2000_vbg.zip': [ROOTDIR / 'data/schutzgebiete', 'http://vogis.cnv.at/geoserver/vogis/ows?service=WFS&version=1.1.0&request=GetFeature&srsName=EPSG:3857&typeName=vogis:natura_2000&maxFeatures=50000&outputFormat=SHAPE-ZIP'],
    'natura_2000_stmk.zip' :[ROOTDIR / 'data/schutzgebiete', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/Europaschutzgebiete.zip'],
    'natura_2000_ktn.zip': [ROOTDIR / 'data/schutzgebiete', 'https://gis.ktn.gv.at/OGD/INSPIRE/PS_ProtectedSite_KTN_GPKG.zip'],
    'natura_2000_ooe.zip': [ROOTDIR / 'data/schutzgebiete', 'https://e-gov.ooe.gv.at/at.gv.ooe.dorisdaten/DORIS_U/VWNATUR_EUSCHUTZGEBIETE_DKM.zip'],
    'natura_2000_vs_sbg.zip': [ROOTDIR / 'data/schutzgebiete', 'https://www.salzburg.gv.at/ogd/36548839-fe5e-4148-ae1d-a3f0fc88fba1/Europaschutzgebiete_VS_RL_Shapefile.zip'],
    'natura_2000_vs_vie.zip': [ROOTDIR / 'data/schutzgebiete', 'https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:NATURA2TVOGELOGD&srsName=EPSG:4326&outputFormat=shape-zip'],
    'natura_2000_vs_noe.zip': [ROOTDIR / 'data/schutzgebiete', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RNA_N2K_VS&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
    'natura_2000_vs_tir.zip': [ROOTDIR / 'data/schutzgebiete', 'http://gis.tirol.gv.at/inspire/downloadservice/Natura2000_Vogelschutzrichtlinie_ETRS89UTM32N.zip'],
    'natura_2000_vs_bgl.zip': [ROOTDIR / 'data/schutzgebiete', 'https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=N2000_VOGELSCHUTZRICHTLINIE.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4&cHash=2d47869118468745c88155103a546cfe'],
    'natura_2000_ffh_noe.zip': [ROOTDIR / 'data/schutzgebiete', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RNA_N2K_FFH&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
    'natura_2000_ffh_sbg.zip': [ROOTDIR / 'data/schutzgebiete', 'https://www.salzburg.gv.at/ogd/7c30326b-fec8-4e85-bb03-65796cc3d63d/Europaschutzgebiete_FFH_RL_Shapefile.zip'],
    'natura_2000_ffh_vie.zip': [ROOTDIR / 'data/schutzgebiete', 'https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:NATURA2TOGD&srsName=EPSG:4326&outputFormat=shape-zip'],
    'natura_2000_ffh_tir.zip': [ROOTDIR / 'data/schutzgebiete', 'http://gis.tirol.gv.at/inspire/downloadservice/Natura2000_FFH_Richtlinie_ETRS89UTM32N.zip'],
    'natura_2000_ffh_bgl.zip': [ROOTDIR / 'data/schutzgebiete', 'https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=N2000_HABITATRICHTLINIE.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4&cHash=0bbfac0c2f3931d334e3ee13c50e92f5'],
}

# %% get data_dict data0
for file, addr in data_dict.items():
    if not os.path.exists(addr[0]):
        os.mkdir(addr[0])
    download_file(addr[1], addr[0] / file)
    if file[-3:] == 'zip':
        with zipfile.ZipFile(addr[0] / file) as zip_ref:
            zip_ref.extractall(addr[0])
