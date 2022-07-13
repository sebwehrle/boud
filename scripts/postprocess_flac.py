# %% imports
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import gamstransfer as gt
import matplotlib.pyplot as plt

from config import ROOTDIR, country
from src.funs import sliced_location_optimization, locations_to_gdf, array_clip

# %% input & data
austria = gpd.read_file(ROOTDIR / 'data/vgd/vgd_oesterreich.shp')
austria = austria[['BL', 'geometry']].dissolve(by='BL')
austria.reset_index(inplace=True)

zones = {
    'Niederösterreich': ROOTDIR / 'data/zones/Zonierung_noe.shp',
    'Burgenland': ROOTDIR / 'data/zones/Widmungsflaechen_bgld.shp',
    'Steiermark': ROOTDIR / 'data/zones/Zonierung_stmk.shp',
}

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

cf = xr.open_dataarray(ROOTDIR / f'data/preprocessed/capacity_factors_{country}.nc')
cf = cf.squeeze()
cf = cf.rio.reproject(austria.crs)

energy = xr.open_dataarray(ROOTDIR / f'data/results/energy_generation_{country}.nc')
energy = energy.drop_vars('turbine_models')
energy = energy.rio.reproject(austria.crs)
energy = energy * 0.85

power = xr.open_dataarray(ROOTDIR / f'data/results/installed_power_{country}.nc')
power = power.rio.write_crs('epsg:3416')
power = power.rio.reproject(austria.crs)

# %% plots of estimation results
# valuated flac prediction
fex = pd.read_csv(ROOTDIR / 'data/externality_state.csv')
fex.index = pd.MultiIndex.from_arrays([fex['y'], fex['x']])
fex = fex['externality']
fax = fex.to_xarray()
fax.name = 'Opportunity Cost [€/MWh]'

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
fax.plot(ax=ax, vmin=0, vmax=75)
plt.axis('off')
plt.tight_layout()
plt.savefig(ROOTDIR / 'figures/OpCo_LowerAustria.png', dpi=200)

# probability plot
prb = pd.read_csv(ROOTDIR / 'data/prob_state.csv')
prb.index = pd.MultiIndex.from_arrays([prb['y'], prb['x']])
prb = prb['probability']
prb = prb.to_xarray()

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
prb.plot(ax=ax, vmin=0, vmax=0.2)
zoning.boundary.plot(ax=ax, color='red')
plt.axis('off')
plt.savefig(ROOTDIR / 'figures/Prob_LowerAustria.png', dpi=200)
plt.close()

# valuation for all of Austria
bundesland = austria.loc[austria['BL'] == 'Niederösterreich', :]
cfnoe = cf.rio.clip(bundesland.geometry, bundesland.crs)
exeuro = fax.interp_like(cfnoe) * cfnoe * 8760 * 0.85
exeuro.name = """Implied External Cost ['000 €]"""

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
(exeuro/1000).plot(ax=ax, vmin=0, vmax=200)
plt.axis('off')
plt.title('')
plt.tight_layout()
plt.savefig(ROOTDIR / 'figures/externality_state.png', dpi=200)

# opportunity cost for all of Austria
fexa = pd.read_csv(ROOTDIR / 'data/externality_aut.csv')
fexa.index = pd.MultiIndex.from_arrays([fexa['y'], fexa['x']])
fexa = fexa['externality']
faxa = fexa.to_xarray()
faxa.name = 'Opportunity Cost [€/MWh]'


fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(16, 6))
faxa.plot(ax=ax, vmin=0, vmax=75)
plt.axis('off')
plt.tight_layout()
plt.savefig(ROOTDIR / 'figures/OpCo_Austria.png', dpi=200)

# implied external cost for all of Austria
ex_aut_eur = faxa.interp_like(cf) * cf * 8760 * 0.85 / 1000
ex_aut_eur.name = """Implied External Cost ['000 €]"""

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(16, 6))
ex_aut_eur.plot(ax=ax, vmin=0, vmax=250)
plt.axis('off')
plt.title('')
plt.tight_layout()
plt.savefig(ROOTDIR / 'figures/externality_Austria.png', dpi=200)

# probability for all of Austria
prba = pd.read_csv(ROOTDIR / 'data/prob_austria.csv')
prba.index = pd.MultiIndex.from_arrays([prba['y'], prba['x']])
prba = prba['probability']
prba = prba.to_xarray()

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(16, 6))
prba.plot(ax=ax, vmin=0, vmax=0.125)
zoning.boundary.plot(ax=ax, color='red')
plt.axis('off')
plt.savefig(ROOTDIR / 'figures/Prob_Austria.png', dpi=200)
plt.close()

# %% optimal turbine allocation
gams_dict = {
    'gams_model': ROOTDIR / 'opt/location_selection.gms',
    'gdx_input': ROOTDIR / 'opt/input_data.gdx',
    'gdx_output': ROOTDIR / 'opt',
    'gams_exe': Path('c:/myprogs/gams/39')
}

tcost = pd.read_csv(ROOTDIR / 'data/total_cost_austria.csv')
tcost.index = pd.MultiIndex.from_arrays([tcost['y'], tcost['x']])
tcost = tcost['cost']
tcost_array = tcost.to_xarray()
tcost_array = tcost_array.rio.write_crs(austria.crs)


gams_transfer_container = gt.Container()
nslices = 50
nturbines = 'auto'
locations = sliced_location_optimization(gams_dict, gams_transfer_container, tcost_array,
                                         num_slices=nslices, space_px=3, num_turbines=nturbines, read_only=False)

soco = [locations_to_gdf(tcost_array, locations[i*nturbines:(i+1)*nturbines], energy_array=energy, power_array=power)
        for i in range(0, nslices)]
soco = pd.concat(soco)
soco = soco.dropna(how='any', axis=0)
soco = soco.sort_values(by='LCOE')

soco['CumEnergy'] = soco['Energy'].cumsum() / 1000
soco.to_csv(ROOTDIR / f'data/optimal_turbines_{nslices}_{nturbines}.csv')

goco = soco.to_crs('epsg:4326')
# turbine in standing waters (Neusiedler See),
goco['x'] = goco.geometry.x
goco['y'] = goco.geometry.y
goco[['y', 'x']].to_csv(ROOTDIR / f'data/turbine_locations_{nslices}_{nturbines}.csv')

  # %% plots of turbine siting
fig, ax = plt.subplots(1, 1)
plt.plot(soco['Energy'].cumsum()/1000, soco['LCOE'], color='blue')
plt.show()

fig, ax = plt.subplots(1, 1)
austria.boundary.plot(ax=ax)
soco.loc[soco['CumEnergy'] <= 300, :].plot(ax=ax)
plt.show()

# %%
def xy_plot(x1, x2, y1, y2, label1, label2, ylim, ylabel, xlabel, title, savepath):
    fig, ax = plt.subplots(1, 1)
    plt.plot(x1, y1, color='blue', label=label1)
    plt.plot(x2, y2, color='green', label=label2)
    ax.set_ylim(ylim)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    plt.title(title)
    plt.legend()
    plt.grid()
    plt.savefig(savepath)
    plt.show()
    plt.close()


# plot locations and cost

# plot supply curve - energy

# plot supply curve - power
