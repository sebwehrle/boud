# %% imports
import pandas as pd
import geopandas as gpd
from config import ROOTDIR
import matplotlib.pyplot as plt

# settings
dca = ROOTDIR / 'data/schutzgebiete'
target_projection = 'epsg:3416'
common_columns = ['BUNDESLAND', 'geometry']


# %% combine shapefiles
def combine_shapefiles(directory, fname, iterator):
    gdf = gpd.GeoDataFrame()
    for i in iterator:
        shp = gpd.read_file(directory / f'{fname}_{i}.shp')
        gdf = pd.concat([gdf, shp], axis=0, join='outer')
    return gdf


wdpa = combine_shapefiles(dca, 'WDPA_WDOECM_Jun2022_Public_AUT_shp-polygons', [1, 2, 3])

cats = wdpa['IUCN_CAT'].unique()
cats = ['Ia', 'Ib', 'II', 'III', 'IV', 'V', 'VI', 'Not Reported', 'Not Applicable']

# 'II' contains ['National Park', 'Biosphere Park']
# 'III' contains ['Nature Reserve', 'Protected Landscape Section', 'Protected Natural Objects of local importance',
# 'protected biotopes', 'regional protected areas']  ('Naturschutzgebiet', 'Geschützter Landschaftsteil',
# 'Geschützte Naturgebilde von örtlicher Bedeutung', 'Geschützte Biotope', 'Örtliche Schutzgebiete')
# 'IV' contains ['landscape and nature protection area', 'Nature Reserve', 'Protected Landscape Section',
# 'Flora Protection Area', 'Rest Area', 'Nature Park', 'special conservation areas', 'Landscape Protection Area',
# 'Protected Habitat', 'Ecological Development Area']
# 'V' contains ['Landscape Protection Area', 'Nature Park', 'Protected Landscape Section', 'Flora Protection Area',
# 'ex-lege landscape protection', 'National Park', 'Biosphere Park']

# 'Not Reported includes [Ramsar, Birds Directive, Habitats Directive]


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


iucn_cats = ['Ia', 'Ib', 'II', 'III', 'IV', 'V', 'VI']
wdpa_subcats = ['Birds', 'Habitats', 'Ramsar']
protected_areas = wdpa_categories(wdpa, iucn_cats, wdpa_subcats)



"""
# %%
wdpa_cat = wdpa.loc[wdpa['IUCN_CAT'] == 'VI', :]
desigs = wdpa_cat['DESIG_ENG'].unique()
desigs
len(wdpa_cat)

wdpa_naturepark = wdpa.loc[wdpa['DESIG_ENG'].str.contains('Nature Park'), :]

wproa = wdpa.loc[wdpa['DESIG_ENG'].str.contains('World Heritage'), :]

ramsar = wdpa.loc[wdpa['DESIG_ENG'].str.contains('Ramsar'), :]
birds = wdpa.loc[wdpa['DESIG_ENG'].str.contains('Birds Directive'), :]
habitat = wdpa.loc[wdpa['DESIG_ENG'].str.contains('Habitats Directive'), :]

# %% functions
def process_protected_areas(directory, file_dict, common_columns, target_projection):

    collection = gpd.GeoDataFrame()
    for state, props in file_dict.items():
        gdf = gpd.read_file(directory / props[0])
        gdf['BUNDESLAND'] = state
        if props[1] is not None:
            gdf = gdf.loc[gdf[props[1][0]].str.contains(props[1][1])]
        gdf = gdf.to_crs(target_projection)
        collection = pd.concat([collection, gdf[common_columns]])
    collection = collection.dissolve(by='BUNDESLAND')
    collection = collection.reset_index()
    return collection


# %% Nationalparks
nat_parks = gpd.read_file(dca / 'nationalparks.shp')
nat_parks = nat_parks.to_crs(target_projection)

# %% natura 2000 flora-fauna-habitat
ffh_collection = {
    'Burgenland': ['natura_2000_ffh_bgl.shp', None],
    'Niederösterreich': ['natura_2000_ffh_noe.shp', None],
    'Steiermark': ['natura_2000_stmk.shp', ('KATEGORIE', 'Fauna Flora')],
    'Wien': ['natura_2000_ffh_vie.shp', None],
    'Oberösterreich': ['natura_2000_ooe.shp', ('Bezeichnun', 'FFH')],
    # 'Kärnten': [],
    'Salzburg': ['natura_2000_ffh_sbg.shp', ('stype', 'FFH-RL')],
    'Tirol': ['Natura2000_FFH.gml', None],
    'Vorarlberg': ['natura_2000_vbg.shp', ('eu_typ', 'SCI|SAC')]
}

ffh = process_protected_areas(dca/'natura', ffh_collection, common_columns, target_projection)

# %% natura 2000 vogelschutz
vs_collection = {
    'Burgenland': ['natura_2000_vs_bgl.shp', None],
    'Niederösterreich': ['natura_2000_vs_noe.shp', None],
    'Steiermark': ['natura_2000_stmk.shp', ('KATEGORIE', 'Vogelschutz')],
    'Wien': ['natura_2000_vs_vie.shp', ('BEZEICHNUN', 'Vogelschutz')],
    'Oberösterreich': ['natura_2000_ooe.shp', ('Bezeichnun', 'Vogelschutz')],
    # 'Kärnten': [],
    'Salzburg': ['natura_2000_vs_sbg.shp', ('stype', 'VS-RL')],
    'Tirol': ['Natura2000_SPA.gml', None],
    'Vorarlberg': ['natura_2000_vbg.shp', ('eu_typ', 'SPA')]
}

vs = process_protected_areas(dca/'natura', vs_collection, common_columns, target_projection)

# %% ramsar gebiete
ramsar_collection = {
    'Burgenland': ['ramsar_bgl.shp', ('TYP', 'Ramsar')],
    'Niederösterreich': ['ramsar_noe.shp', None],
    'Steiermark': ['ramsar_stmk.shp', ('KATEGORIE', 'Ramsar')],
    #'Wien': ['NATURA2TVOGELOGDPolygon.shp', ('BEZEICHNUN', 'Ramsar')],
    'Oberösterreich': ['ramsar_ooe.shp', ('Designatio', 'ramsar')],
    # 'Kärnten': [],
    'Salzburg': ['ramsar_sbg.shp', ('kategorie', 'Ramsar')],
    'Tirol': ['Ramsar_Gebiete.gml', None],
    #'Vorarlberg': ['natura_2000.shp', ('eu_typ', 'SPA')]
}

ramsar = process_protected_areas(dca/'ramsar', ramsar_collection, common_columns, target_projection)

# %% Naturschutzgebiete
nature_conservation_collection = {
    'Burgenland': ['naturschutz_bgl.shp', ('TYP', 'Naturschutzgebiet')],
    'Niederösterreich': ['naturschutz_noe.shp', None],
    # 'Steiermark': ['naturschutz_stmk.shp', None],
    'Wien': ['naturschutz_vie.shp', None],
    'Oberösterreich': ['naturschutz_ooe.shp', ('Ordnungsty', 'Naturschutzgebiet')],
    # 'Kärnten': ['naturschutz_ktn.shp', None],
    'Salzburg': ['naturschutz_sbg.shp', None],
    'Tirol': ['ps_SchutzgebieteNaturschutzgesetz.gml', ('text', 'Naturschutzgebiet')],
    'Vorarlberg': ['naturschutz_vbg.shp', ('kategorie', 'Naturschutzgebiet')],
}
# TODO: Steiermark provides 3 ns-files with lit a, b, c categories
# TODO: troubles with encoding in noe text

nsg = process_protected_areas(dca/'naturschutz', nature_conservation_collection, common_columns, target_projection)

# %% Biosphärenparks
biosphere_collection = {
    'Burgenland': [],
    'Niederösterreich': [],
    'Steiermark': [],
    'Wien': [],
    'Oberösterreich': [],
    'Kärnten': [],
    'Salzburg': [],
    'Tirol': [],
    'Vorarlberg': [],
}


# %% Landschaftsschutzgebiete
landscape_collection = {
    'Burgenland': [],
    'Niederösterreich': [],
    'Steiermark': [],
    'Wien': [],
    'Oberösterreich': [],
    'Kärnten': [],
    'Salzburg': [],
    'Tirol': [],
    'Vorarlberg': [],
}



# %% Naturparks
nature_park_collection = {
    'Burgenland': [],
    'Niederösterreich': [],
    'Steiermark': [],
    'Wien': [],
    'Oberösterreich': [],
    'Kärnten': [],
    'Salzburg': [],
    'Tirol': [],
    'Vorarlberg': [],
}


#%%
gdf = gpd.read_file(dca/'wdpa/2/WDPA_WDOECM_Jun2022_Public_AUT_shp-polygons.shp')
"""
