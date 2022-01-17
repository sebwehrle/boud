# %% imports
import os
import json
import shutil

import numpy as np
import urllib3
import certifi
import pandas as pd

from config import ROOTDIR


# %% define functions
def download_data(url, save_to):
    http = urllib3.PoolManager(ca_certs=certifi.where())
    with http.request('GET', url, preload_content=False) as r, open(save_to, 'wb') as out_file:
        shutil.copyfileobj(r, out_file)


# %% process data
if not os.path.exists(ROOTDIR / 'data/AT_turbines'):
    os.mkdir(ROOTDIR / 'data/AT_turbines')

igwurl = 'https://www.igwindkraft.at/src_project/external/maps/generated/gmaps_daten.js'
download_data(igwurl, ROOTDIR / 'data/AT_turbines/igwind.js')

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
igw['Type'] = igw['Type'].replace(streptyp)
igw['Hersteller'] = igw['Hersteller'].replace(strepher)

# clean Types
igw.loc[(igw['Type'] == 'E40') & (igw['kW'] == 500), 'Type'] = 'E40 5.40'
igw.loc[(igw['Type'] == 'E40') & (igw['kW'] == 600), 'Type'] = 'E40 6.44'
igw.loc[(igw['Type'] == 'E66') & (igw['kW'] == 1800), 'Type'] = 'E66 18.70'
igw.loc[(igw['Type'] == 'E82') & (igw['kW'] == 2300), 'Type'] = 'E82 E2'
igw.loc[(igw['Type'] == 'E115') & (igw['kW'] == 3200), 'Type'] = 'E115 E2'
igw.loc[(igw['Type'] == 'M114') & (igw['kW'] == 3170), 'Type'] = '3.2M114'

# Add detail for Oberwaltersdorf - source: https://www.ris.bka.gv.at/Dokumente/Bvwg/BVWGT_20150313_W102_2008321_1_00/BVWGT_20150313_W102_2008321_1_00.html
igw.loc[igw['Name'].str.contains('Oberwaltersdorf'), 'Type'] = 'V112'
igw.loc[igw['Name'].str.contains('Oberwaltersdorf'), 'Nabenhöhe'] = '140'
igw.loc[igw['Name'].str.contains('Oberwaltersdorf'), 'Rotordurchmesser'] = '112'

# Add detail for Pretul - source: https://www.bundesforste.at/fileadmin/erneuerbare_energie/Folder_Windpark-Pretul_FINAL_screen.pdf
igw.loc[igw['Name'].str.contains('Pretul'), 'Type'] = 'E82 E4'
igw.loc[igw['Name'].str.contains('Pretul'), 'Betreiber1'] = 'Österreichische Bundesforste'

igw.loc[igw['Nabenhöhe'] == '', 'Nabenhöhe'] = np.nan
igw['Nabenhöhe'] = igw['Nabenhöhe'].astype('float')

igw.loc[igw['Rotordurchmesser'] == '', 'Rotordurchmesser'] = np.nan
igw['Rotordurchmesser'] = igw['Rotordurchmesser'].astype('float')

# %% write files
igw.to_csv(ROOTDIR / 'data/AT_turbines/igwturbines.csv', sep=';', decimal=',', encoding='utf8')

tmod = igw[['Hersteller', 'Type']].drop_duplicates().sort_values(['Hersteller', 'Type'])
