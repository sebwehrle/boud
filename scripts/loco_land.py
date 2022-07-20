# %% imports
from pathlib import Path

import matplotlib.pyplot as plt
import xarray as xr
import rioxarray
import pandas as pd
import geopandas as gpd
import gamstransfer as gt
import matplotlib.pyplot as plt

from config import ROOTDIR, country
from src.funs import sliced_location_optimization, locations_to_gdf

# %% config
gams_dict = {
    'gams_model': ROOTDIR / 'opt/location_selection.gms',
    'gdx_input': ROOTDIR / 'opt/input_data.gdx',
    'gdx_output': ROOTDIR / 'opt',
    'gams_exe': Path('c:/myprogs/gams/39')
}

nslices = 1
nturbines = 'auto'

umlauts = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe', ord('ß'):'ss'}

tuerbchens = {
    'Burgenland': 1600,  # 2000: 0:26:38.697; 1500: 0:08:02.124, 0:08:04.531; 1600:
    'Kärnten': 7000,  # 1500: 0:01:34.211; 2500: 0:01:31.247; 5000: 0:03:45.148; 7000:
    'Niederösterreich': 5000,  # 4000: 0:08:36:379; 5000: 0:14:02.010; 4500: 0:12:58.039
    'Oberösterreich': 5000,  # 2000: 0:02:43.107; 3000: 0:02:32.006; 4000: 0:03:30.443; 5000:
    'Salzburg': 5000,  # 1500: 0:01:51.120; 2500: 0:01:49.859; 4000: 0:03:35.592; 5000:
    'Steiermark': 5000,  # 2000: 0:02:59.648; 2500: 0:02:42.751; 3500: 0:02:49.005; 5000:
    'Tirol': 3500,  # 1000: 0:02:51.202; 1500: 0:02:30.894; 2500: 0:02:38.644; 3500:
    'Vorarlberg': 2500,  # 1000: 0:00:30.763; 2000: 0:04:20.553, 0:04:27.358; 2500:
    'Wien': 1500,  # 1500:
}

# %% location optimization
austria = gpd.read_file(ROOTDIR / 'data/vgd/vgd_oesterreich.shp')
austria = austria[['BL', 'geometry']].dissolve(by='BL')
austria.reset_index(inplace=True)

dta = pd.read_csv(ROOTDIR / 'data/vars_austria_touched.csv')
dta.index = pd.MultiIndex.from_arrays([dta['y'], dta['x']])
dta = dta.drop(['x', 'y'], axis=1)
dta_ray = dta.to_xarray()
dta_ray = dta_ray.rio.write_crs(austria.crs)

toco = pd.read_csv(ROOTDIR / 'data/total_cost_austria.csv')
toco.index = pd.MultiIndex.from_arrays([toco['y'], toco['x']])
toco = toco['cost']
toco_ray = toco.to_xarray()
toco_ray = toco_ray.rio.write_crs(austria.crs)


# %%
energy = dta_ray['generation']
power = energy.copy()
power = xr.where(~power.isnull(), 3.05, power)
power = power.rio.write_crs(austria.crs)

locos = []
for land in austria.BL.unique():
    gams_transfer_container = gt.Container()

    nturbines = tuerbchens[land]
    bundesland = austria.loc[austria['BL'] == land, :]
    toco_land = toco_ray.rio.clip(bundesland.geometry, bundesland.crs)
    energy_land = energy.rio.clip(bundesland.geometry, bundesland.crs)
    power_land = power.rio.clip(bundesland.geometry, bundesland.crs)
    print(f'Optimizing {land}')
    locations = sliced_location_optimization(gams_dict, gams_transfer_container, toco_land, max_turbines=10000,
                                             num_slices=nslices, space_px=3, num_turbines=nturbines,
                                             gdx_out_string=f'{land.translate(umlauts)}', read_only=False)
    locations = locations_to_gdf(toco_land, locations, energy_array=energy_land, power_array=power_land)
    locos.append(locations)

loca = pd.concat(locos)

# %% generate supply curve
loca = loca.sort_values(by='LCOE')
loca['CumEnergy'] = loca['Energy'].cumsum() / 1000
loca = loca.reset_index(drop=True)
loca.to_csv(ROOTDIR / 'data/results/locations_socopt.csv')

# %% plot
nrg_gwh = 17000

fig, ax = plt.subplots(1, 1)
austria.plot(ax=ax)
loca.loc[loca.CumEnergy <= nrg_gwh, :].plot(ax=ax, marker='.', markersize=1.0, color='red')
plt.title(f'Socially optimal locations for annual generation of {nrg_gwh/1000} TWh')
plt.axis('off')
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(1, 1)
plt.plot(loca['Energy'].cumsum()/1000, loca['LCOE'], color='blue')
plt.grid()
plt.show()

# %% optimize for lcoe
lcoe = dta_ray['lcoe']

locos = []
for land in austria.BL.unique():
    gams_transfer_container = gt.Container()

    nturbines = tuerbchens[land]
    bundesland = austria.loc[austria['BL'] == land, :]
    lcoe_land = lcoe.rio.clip(bundesland.geometry, bundesland.crs)
    energy_land = energy.rio.clip(bundesland.geometry, bundesland.crs)
    power_land = power.rio.clip(bundesland.geometry, bundesland.crs)
    print(f'Optimizing {land}')
    locations = sliced_location_optimization(gams_dict, gams_transfer_container, lcoe_land, max_turbines=10000,
                                             num_slices=nslices, space_px=3, num_turbines=nturbines,
                                             gdx_out_string=f'{land.translate(umlauts)}', read_only=False)
    locations = locations_to_gdf(lcoe_land, locations, energy_array=energy_land, power_array=power_land)
    locos.append(locations)

locl = pd.concat(locos)
locl = locl.sort_values(by='LCOE')
locl['CumEnergy'] = locl['Energy'].cumsum() / 1000
locl.to_csv(ROOTDIR / 'data/results/locations_prvopt.csv')

# %% plotting
nrg_gwh = 17000

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 4))
#fig.suptitle(f'Optimal wind turbine allocations for an annual generation of {nrg_gwh/1000} TWh')

austria.plot(ax=ax1)
loca.loc[loca.CumEnergy <= nrg_gwh, :].plot(ax=ax1, marker='.', markersize=1.0, color='yellow')
ax1.set_title(f'(a) Socially optimal')
ax1.axis('off')
#plt.tight_layout()
#plt.savefig(ROOTDIR / 'figures/OptAlloc_SocAT.png', dpi=200)
#plt.show()

#fig, ax = plt.subplots(1, 1)
austria.plot(ax=ax2)
locl.loc[locl.CumEnergy <= nrg_gwh, :].plot(ax=ax2, marker='.', markersize=1.0, color='red')
ax2.set_title(f'(b) Privately optimal')
ax2.axis('off')
plt.tight_layout()
plt.savefig(ROOTDIR / 'figures/spatial_alloc.png', dpi=200)


# %% Suppy curve
fig, ax = plt.subplots(1, 1)
plt.plot(loca['Energy'].cumsum()/10**6, loca['LCOE'], color='blue')
plt.plot(locl['Energy'].cumsum()/10**6, locl['LCOE'], color='green')
ax.set_ylim([60, 85])
ax.set_xlim([0, 100])
ax.set_xlabel('Expected Annual Wind Power Generation [TWh]')
ax.set_ylabel('Social Cost [€/MWh]')
plt.grid()
plt.show()

# %% export for data validation
vld = loca.copy()
vld = vld.to_crs('epsg:4316')
vld['x'] = vld.geometry.x
vld['y'] = vld.geometry.y
vld.to_csv(ROOTDIR / 'data/validate_socop.csv')
