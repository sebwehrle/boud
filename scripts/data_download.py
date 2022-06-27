# %% imports
import os
import json
import zipfile
import numpy as np
import pandas as pd

from config import ROOTDIR, country
from src.utils import download_file

# %% global wind atlas settings
# TODO: remove creds = 'DWSTW/netw4j:BoogiWuugy44-'
# TODO: remove proxy = 'proxy.wstw.energy-it.net:8080'
url_gwa = 'https://globalwindatlas.info/api/gis/country'
# country = [country]
layer = ['air-density', 'combined-Weibull-A', 'combined-Weibull-k']
ground = ['elevation_w_bathymetry']
height = ['50', '100', '150']

# %% file, directory, url dict
data_dict = {
    # 'rnj_power_curve_000-smooth.csv': [ROOTDIR / 'data/power_curves', 'https://raw.githubusercontent.com/renewables-ninja/vwf/master/power_curves/Wind%20Turbine%20Power%20Curves%20%7E%205%20(0.01ms%20with%200.00%20w%20smoother).csv'],
    # 'oep_wind_turbine_library.zip': [ROOTDIR / 'data/power_curves', """ "https://openenergy-platform.org/api/v0/schema/supply/tables/wind_turbine_library/rows/?form=datapackage" """],
    # 'sam_wind_turbines.csv': [ROOTDIR / 'data/power_curves', 'https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/Wind%20Turbines.csv'],
    # 'vgd_oesterreich.zip': [ROOTDIR / 'data/vgd', """ "https://data.bev.gv.at/download/Verwaltungsgrenzen/shp/20211001/VGD_Oesterreich_gst_20211001.zip" """],
    # 'CLC_2018_AT.zip': [ROOTDIR / 'data/clc', 'https://docs.umweltbundesamt.at/s/beBw8fmwyCMA2ga/download/CLC_2018_AT_clip.zip'],
    # 'gridkit_europe.zip': [ROOTDIR / 'data/grid', 'https://zenodo.org/record/47317/files/gridkit_euorpe.zip?download=1'],
    # 'Zonierung_noe.zip': [ROOTDIR / 'data/zones', """ "https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RRU_WIND_ZONEN_P19&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8" """],
    # 'Widmungsflaechen_bgld.zip': [ROOTDIR / 'data/zones', """ "https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=WIDMUNGSFLAECHEN.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4" """],
    # 'Zonierung_stmk.zip': [ROOTDIR / 'data/zones', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/SAPRO_Windenergie_zone.zip'],
    # 'Ausschlusszone_ooe.zip': [ROOTDIR / 'data/zones', 'https://e-gov.ooe.gv.at/at.gv.ooe.dorisdaten/DORIS_U/WINDKRAFT_AUSSCHLUSSZONE.zip'],
    # f'wdpa_{country}.zip': [ROOTDIR / 'data/schutzgebiete', f'https://d1gam3xoknrgr2.cloudfront.net/current/WDPA_WDOECM_Jun2022_Public_{country}_shp.zip'],
    # 'B_gip_network_ogd.zip': [ROOTDIR / 'data/gip', 'https://open.gip.gv.at/ogd/B_gip_network_ogd.zip'],
    # 'Fliessgewaesser.zip': [ROOTDIR / 'data/water_bodies', 'https://docs.umweltbundesamt.at/s/YkgTDiDs9DPstCJ/download/Routen_v16.zip'],
    #'StehendeGewaesser.zip': [ROOTDIR / 'data/water_bodies', 'https://docs.umweltbundesamt.at/s/t4jHoXmrwrsjnea/download/stehendeGewaesser_v16.zip',],
    #'Widmungen_noe.zip': [ROOTDIR / 'data/landuse', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RRU_WI_HUELLE&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
    #'Erhaltenswerte_gebäude.zip': [ROOTDIR / 'data/landuse', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RRU_WI_GEB&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
    'Adressregister.zip': [ROOTDIR / 'data/gwr', 'https://www.bev.gv.at/pls/portal/docs/PAGE/BEV_PORTAL_CONTENT_ALLGEMEIN/0200_PRODUKTE/UNENTGELTLICHE_PRODUKTE_DES_BEV/Adresse-Relationale_Tabellen_Stichtagsdaten_03042022.zip'],
    # TODO: kagis broken 'elevation.zip': [ROOTDIR / 'data/elevation', 'http']
}

# http://apps.vorarlberg.at/gis_metadatensuche/

# %% download global wind atlas
if not os.path.exists(ROOTDIR / 'data/gwa3'):
    os.mkdir(ROOTDIR / 'data/gwa3')

for c in [country]:
    for l in layer:
        for h in height:
            fname = f'{c}_{l}_{h}.tif'
            download_file(f'{url_gwa}/{c}/{l}/{h}', ROOTDIR / 'data/gwa3' / fname)
    for g in ground:
        fname = f'{c}_{g}.tif'
        download_file(f'{url_gwa}/{c}/{g}', ROOTDIR / 'data/gwa3' / fname)

# %% download data_dict data
for file, addr in data_dict.items():
    if not os.path.exists(addr[0]):
        os.mkdir(addr[0])
    os.chdir(addr[0])
    download_file(addr[1], addr[0] / file)
    if file[-3:] == 'zip':
        with zipfile.ZipFile(addr[0] / file) as zip_ref:
            zipinfos = zip_ref.infolist()
            zipext = [zifo.filename[-3:] for zifo in zipinfos]
            if 'shp' in zipext:
                for zipinf in zipinfos:
                    zipinf.filename = f'{file[0:-3]}{zipinf.filename[-3:]}'
                    zip_ref.extract(zipinf)
            else:
                zip_ref.extractall(addr[0])
    n = 0
    for fname in os.listdir(addr[0]):
        if fname.endswith('.zip'):
            with zipfile.ZipFile(addr[0] / fname) as nested_zip:
                nzipinfos = nested_zip.infolist()
                nzipext = [nzifo.filename[-3:] for nzifo in nzipinfos]
                if 'shp' in nzipext:
                    for nzipinf in nzipinfos:
                        nzipinf.filename = f'{nzipinf.filename[0:-4]}_{n}.{nzipinf.filename[-3:]}'
                        nested_zip.extract(nzipinf)
            n += 1


# %% settings for downloading and processing wind turbine data from IG Windkraft
igwurl = 'https://www.igwindkraft.at/src_project/external/maps/generated/gmaps_daten.js'

streptyp = {
    'E-40': 'E40',
    'E40/5.40': 'E40 5.40',
    'E40 5.4': 'E40 5.40',
    'E66 18.7': 'E66 18.70',
    'E66/18.70': 'E66 18.70',
    'E66.18': 'E66 18.70',
    'E66 20.7': 'E66 20.70',
    'E70/E4': 'E70 E4',
    'E70/20.71': 'E70 E4',
    'E70': 'E70 E4',
    'E-101': 'E101',
    'E 101': 'E101',
    'E115/3.000': 'E115',
    '3.XM': '3XM',
    'V126/3450': 'V126',
}

strepher = {
    'ENERCON': 'Enercon',
    'DeWind': 'Dewind',
}

# %% retrieve and process turbine data

if not os.path.exists(ROOTDIR / 'data/AT_turbines'):
    os.mkdir(ROOTDIR / 'data/AT_turbines')
download_file(igwurl, ROOTDIR / 'data/AT_turbines/igwind.js')

with open(ROOTDIR / 'data/AT_turbines/igwind.js', 'rt') as f:
    with open(ROOTDIR / 'data/AT_turbines/turbines.json', 'wt') as g:
        for line in f:
            g.write(line.replace('var officeLayer = ', ''))
f.close()
g.close()

with open(ROOTDIR / 'data/AT_turbines/turbines.json', 'rt') as k:
    turbson = json.load(k)
k.close()

tlst = []
for i in range(0, len(turbson[1]['places'])):
    tlst.append(turbson[1]['places'][i]['data'])

igw = pd.DataFrame(tlst, columns=['Name', 'Betreiber1', 'Betreiber2', 'n_Anlagen', 'kW', 'Type', 'Jahr', 'x', 'lat',
                                  'lon', 'url', 'Hersteller', 'Nabenhöhe', 'Rotordurchmesser'])

igw['Type'] = igw['Type'].replace(streptyp)
igw['Hersteller'] = igw['Hersteller'].replace(strepher)

# clean Types
igw.loc[(igw['Type'] == 'E40') & (igw['kW'] == 500), 'Type'] = 'E40 5.40'
igw.loc[(igw['Type'] == 'E40') & (igw['kW'] == 600), 'Type'] = 'E40 6.44'
igw.loc[(igw['Type'] == 'E66') & (igw['kW'] == 1800), 'Type'] = 'E66 18.70'
igw.loc[(igw['Type'] == 'E82') & (igw['kW'] == 2300), 'Type'] = 'E82 E2'
igw.loc[(igw['Type'] == 'E115') & (igw['kW'] == 3200), 'Type'] = 'E115 E2'
igw.loc[(igw['Type'] == 'M114') & (igw['kW'] == 3170), 'Type'] = '3.2M114'

# Add detail for Oberwaltersdorf -
# source: https://www.ris.bka.gv.at/Dokumente/Bvwg/BVWGT_20150313_W102_2008321_1_00/BVWGT_20150313_W102_2008321_1_00.html
igw.loc[igw['Name'].str.contains('Oberwaltersdorf'), 'Type'] = 'V112'
igw.loc[igw['Name'].str.contains('Oberwaltersdorf'), 'Nabenhöhe'] = '140'
igw.loc[igw['Name'].str.contains('Oberwaltersdorf'), 'Rotordurchmesser'] = '112'

# Add detail for Pretul -
# source: https://www.bundesforste.at/fileadmin/erneuerbare_energie/Folder_Windpark-Pretul_FINAL_screen.pdf
igw.loc[igw['Name'].str.contains('Pretul'), 'Type'] = 'E82 E4'
igw.loc[igw['Name'].str.contains('Pretul'), 'Betreiber1'] = 'Österreichische Bundesforste'

igw.loc[igw['Nabenhöhe'] == '', 'Nabenhöhe'] = np.nan
igw['Nabenhöhe'] = igw['Nabenhöhe'].astype('float')

igw.loc[igw['Rotordurchmesser'] == '', 'Rotordurchmesser'] = np.nan
igw['Rotordurchmesser'] = igw['Rotordurchmesser'].astype('float')

igw.to_csv(ROOTDIR / 'data/AT_turbines/igwturbines.csv', sep=';', decimal=',', encoding='utf8')
tmod = igw[['Hersteller', 'Type']].drop_duplicates().sort_values(['Hersteller', 'Type'])

# %% Schutzgebiete
# 'nationalparks.zip': [ROOTDIR / 'data/schutzgebiete', 'https://docs.umweltbundesamt.at/s/Ezq6NEJ8LTg6s8j/download/nationalparks_2012.zip'],
# 'natura_2000_vbg.zip': [ROOTDIR / 'data/schutzgebiete/natura', """ "http://vogis.cnv.at/geoserver/vogis/ows?service=WFS&version=1.1.0&request=GetFeature&srsName=EPSG:3857&typeName=vogis:natura_2000&maxFeatures=50000&outputFormat=SHAPE-ZIP" """],
# 'natura_2000_stmk.zip' :[ROOTDIR / 'data/schutzgebiete/natura', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/Europaschutzgebiete.zip'],
# #'natura_2000_ktn.zip': [ROOTDIR / 'data/schutzgebiete/natura', 'https://gis.ktn.gv.at/OGD/INSPIRE/PS_ProtectedSite_KTN_GPKG.zip'],
# 'natura_2000_ooe.zip': [ROOTDIR / 'data/schutzgebiete/natura', 'https://e-gov.ooe.gv.at/at.gv.ooe.dorisdaten/DORIS_U/VWNATUR_EUSCHUTZGEBIETE_DKM.zip'],
# 'natura_2000_vs_sbg.zip': [ROOTDIR / 'data/schutzgebiete/natura', 'https://www.salzburg.gv.at/ogd/36548839-fe5e-4148-ae1d-a3f0fc88fba1/Europaschutzgebiete_VS_RL_Shapefile.zip'],
# 'natura_2000_vs_vie.zip': [ROOTDIR / 'data/schutzgebiete/natura', """ "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:NATURA2TVOGELOGD&srsName=EPSG:4326&outputFormat=shape-zip" """],
# 'natura_2000_vs_noe.zip': [ROOTDIR / 'data/schutzgebiete/natura', """ "https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RNA_N2K_VS&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8" """],
# 'natura_2000_vs_tir.zip': [ROOTDIR / 'data/schutzgebiete/natura', 'https://gis.tirol.gv.at/inspire/downloadservice/Natura2000_Vogelschutzrichtlinie_ETRS89UTM32N.zip'],
# 'natura_2000_vs_bgl.zip': [ROOTDIR / 'data/schutzgebiete/natura', """ "https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=N2000_VOGELSCHUTZRICHTLINIE.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4&cHash=2d47869118468745c88155103a546cfe" """],
# 'natura_2000_ffh_noe.zip': [ROOTDIR / 'data/schutzgebiete/natura', """ "https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RNA_N2K_FFH&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8" """],
# 'natura_2000_ffh_sbg.zip': [ROOTDIR / 'data/schutzgebiete/natura', 'https://www.salzburg.gv.at/ogd/7c30326b-fec8-4e85-bb03-65796cc3d63d/Europaschutzgebiete_FFH_RL_Shapefile.zip'],
# 'natura_2000_ffh_vie.zip': [ROOTDIR / 'data/schutzgebiete/natura', """ "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:NATURA2TOGD&srsName=EPSG:4326&outputFormat=shape-zip" """],
# 'natura_2000_ffh_tir.zip': [ROOTDIR / 'data/schutzgebiete/natura', 'https://gis.tirol.gv.at/inspire/downloadservice/Natura2000_FFH_Richtlinie_ETRS89UTM32N.zip'],
# 'natura_2000_ffh_bgl.zip': [ROOTDIR / 'data/schutzgebiete/natura', """ "https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=N2000_HABITATRICHTLINIE.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4&cHash=0bbfac0c2f3931d334e3ee13c50e92f5" """],
# 'ramsar_bgl.zip': [ROOTDIR / 'data/schutzgebiete/ramsar', """ "https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=RAMSARGEBIET.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4&cHash=169fc3f1511384ebd4a8f8f911448a1e" """],
# 'ramsar_noe.zip': [ROOTDIR / 'data/schutzgebiete/ramsar', """ "https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RNA_RAMSAR&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8" """],
# 'ramsar_ooe.zip': [ROOTDIR / 'data/schutzgebiete/ramsar', 'https://e-gov.ooe.gv.at/at.gv.ooe.dorisdaten/DORIS_U/RAMSAR_GEBIETE.zip'],
# 'ramsar_sbg.zip': [ROOTDIR / 'data/schutzgebiete/ramsar', 'https://www.salzburg.gv.at/ogd/fbb1e8e0-ffd8-45dc-9f60-f49cc0d49227/Gebiete_gem_Ramsar_Konvention_Shapefile.zip'],
# 'ramsar_stmk.zip': [ROOTDIR / 'data/schutzgebiete/ramsar', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/Ramsar_Gebiete.zip'],
# 'ramsar_tir.zip': [ROOTDIR / 'data/schutzgebiete/ramsar', 'https://gis.tirol.gv.at/inspire/downloadservice/Ramsar_ETRS89UTM32N.zip'],
# 'ramsar_ktn.zip': [ROOTDIR / 'data/schutzgebiete/ramsar', 'https://gis.ktn.gv.at/OGD/INSPIRE/PS_ProtectedSite_KTN_GPKG.zip'],
# 'naturschutz_bgl.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://geodaten.bgld.gv.at/de/downloads/fachdaten.html?tx_gisdownloads_gisdownloads%5Bcontroller%5D=Download&tx_gisdownloads_gisdownloads%5Bf%5D=NATURSCHUTZ.zip&tx_gisdownloads_gisdownloads%5Bs%5D=4&cHash=61d8c2a5cad13cd325796381e49f9009'],
# 'naturschutz_noe.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RNA_NSGEB&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
# 'naturschutz_vie.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:NATURSCHUTZGEBOGD&srsName=EPSG:4326&outputFormat=shape-zip'],
# 'naturschutz_stmk_a.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/Naturschutzgebiete_a.zip'],
# 'naturschutz_stmk_b.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/Naturschutzgebiete_b.zip'],
# 'naturschutz_stmk_c.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/Naturschutzgebiete_c.zip'],
# 'naturschutz_ooe.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://e-gov.ooe.gv.at/at.gv.ooe.dorisdaten/DORIS_U/VWNATIONALE_SCHUTZGEBIETE.zip'],
# 'naturschutz_ktn.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://gis.ktn.gv.at/OGD/INSPIRE/PS_ProtectedSite_KTN_GPKG.zip'],
# 'naturschutz_sbg.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'https://www.salzburg.gv.at/ogd/f035e1ef-9b98-4d77-b2ad-1daf6013e6b3/Naturschutzgebiete_Shapefile.zip'],
# 'naturschutz_tir.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'http://gis.tirol.gv.at/inspire/downloadservice/Schutzgebiete_Naturschutzgesetz_ETRS89UTM32N.zip'],
# 'naturschutz_vbg.zip': [ROOTDIR / 'data/schutzgebiete/naturschutz', 'http://vogis.cnv.at/geoserver/vogis/ows?service=WFS&version=1.1.0&request=GetFeature&srsName=EPSG:31254&typeName=vogis:schutzgebiete_naturschutz&outputFormat=shape-zip'],
# 'biosphaere_noe.zip': [ROOTDIR / 'data/schutzgebiete/biosphaere', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RRU_BPWW_PFLEGEZONEN&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
# 'biosphaere_vie.zip': [ROOTDIR / 'data/schutzgebiete/biosphaere', 'https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:BIOSPHPARKFOGD&srsName=EPSG:4326&outputFormat=shape-zip'],
# 'biosphaere_stmk': [ROOTDIR / 'data/schutzgebiete/biosphaere', ],  # Unteres Murtal
# 'biosphaere_ktn': [ROOTDIR / 'data/schutzgebiete/biosphaere', ],  # Nockberge
# 'biosphaere_sbg.zip': [ROOTDIR / 'data/schutzgebiete/biosphaere', 'https://www.salzburg.gv.at/ogd/ed762722-d8c2-431b-bf5d-bf6f1d125916/Biosphaerenpark_Shapefile.zip'],
# 'biosphaere_vbg': [ROOTDIR / 'data/schutzgebiete/biosphaere', ],  # Großes Walsertal
# 'landschaftschutz_bgl': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', ],
# 'landschaftschutz_noe.zip': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', 'https://sdi.noe.gv.at/at.gv.noe.geoserver/OGD/wfs?request=GetFeature&version=1.1.0&typeName=OGD:RNA_LSGEB&srsName=EPSG:31259&outputFormat=shape-zip&format_options=CHARSET:UTF-8'],
# 'landschaftschutz_vie.zip': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', 'https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:LANDSCHUTZGEBOGD&srsName=EPSG:4326&outputFormat=shape-zip'],
# 'landschaftschutz_stmk.zip': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', 'https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/Landschaftsschutzgebiete.zip'],
# 'landschaftschutz_ooe': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', ],
# 'landschaftschutz_ktn': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', ],
# 'landschaftschutz_sbg.zip': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', 'https://www.salzburg.gv.at/ogd/8fca789d-988f-404a-97d8-a8c2d417d766/Landschaftsschutzgebiete_Shapefile.zip'],
# 'landschaftschutz_tir': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', ],
# 'landschaftschutz_vbg.zip': [ROOTDIR / 'data/schutzgebiete/landschaftschutz', ],  # included in naturschutz_vbg.zip
# 'naturdenkmale_bgl': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_noe': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_vie': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_stmk': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_ooe': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_ktn': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_sbg': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_tir': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],
# 'naturdenkmale_vbg': [ROOTDIR / 'data/schutzgebiete/naturdenkmale', ],