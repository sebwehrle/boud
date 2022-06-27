# %% description of workflow running wind turbine impact assessment

# 1) adjust settings in config.py

# %% 2) download data
#    input: config.py, data urls
data_download.py

# %% pre-process geodata
preprocess_geodata.py

# %% 3) pre-process data
#    input: power curve data, GWA3 data
#    output: powercurves.csv, gwa_air_density.nc, gwa_roughness.nc
preprocessing.py

# %% 4) distance calculation
#    input: GWA3 combined Weibull, VGD.shp, gridkit_europe_highvoltage_links.csv, CLC18_AT_clip.shp
#    output: grid_distance.nc
distances.py

# %% 5) capacity factor computation
#    input: GWA3 combined Weibull A and k, gwa_roughnes.nc, gwa_air_density.nc, powercurves.csv
#    output: capacity_factors.nc
capacity_factor.py

# %% 6) compute levelized cost of electricity
#    input: manual settings, capacity_factors-nc, grid_distances.nc, powercurves.csv
#    output: lcoe.nc
# TODO: include terrain steepness and distance to major roads in investment cost calculation
lcoe.py

# %% process restrictions on turbine placement
#    input: nature conservation areas, settlements,
#    output:


# %% 8) determine optimal turbine spacing
#    input:
#    output:
zoning.py

# %% 9) convert turbine locations to installed capacity and generated electricity


power_energy.py


