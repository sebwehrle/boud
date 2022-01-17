# %% imports
import os
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import itertools
import subprocess
from operator import itemgetter
from scipy.spatial import KDTree
from shapely.ops import substring
from shapely.geometry import Point, LineString
import gamstransfer as gt


# %% capacity factor functions
def weibull_probability_density(u_power_curve, k, A):
    """
    Calculates probability density at points in u_power_curve given Weibull parameters in k and A
    :param u_power_curve:
    :param k:
    :param A:
    :return:
    """
    uar = np.asarray(u_power_curve)
    prb = [(k / A * (z / A) ** (k - 1)) * (np.exp(-(z / A) ** k)) for z in uar]
    pdf = xr.concat(prb, dim='wind_speed')
    pdf = pdf.assign_coords({'wind_speed': u_power_curve})
    pdf = pdf.squeeze()
    return pdf


def capacity_factor(pdf, alpha, u_power_curve, p_power_curve, h_turbine, h_reference=100):
    """
    calculates wind turbine capacity factors given Weibull probability density pdf, roughness factor alpha, wind turbine
    power curve data in u_power_curve and p_power_curve, turbine height h_turbine and reference height of wind speed
    modelling h_reference
    :param pdf: probability density function from weibull_probability_density()
    :param alpha: roughness coefficient
    :param u_power_curve:
    :param p_power_curve:
    :param h_turbine:
    :param h_reference:
    :return:
    """
    power_curve = xr.DataArray(data=p_power_curve, coords={'wind_speed': u_power_curve})
    u_adjusted = xr.DataArray(data=u_power_curve, coords={'wind_speed': u_power_curve}) @ (h_turbine/h_reference)**alpha
    cap_factor_values = np.trapz(pdf * power_curve, u_adjusted, axis=0)
    cap_factor = alpha.copy()
    cap_factor.values = cap_factor_values
    return cap_factor


# %% LCOE functions
def turbine_overnight_cost(power, hub_height, rotor_diameter, year):
    """
    calculates wind turbine investment cost in EUR per kw
    :param power: im MW
    :param hub_height: in m
    :param rotor_diameter: in m
    :return: overnight investment cost in EUR per kW
    """
    rotor_area = np.pi * (rotor_diameter / 2) ** 2
    spec_power = power * 10**6 / rotor_area
    cost = (620 * np.log(hub_height)) - (1.68 * spec_power) + (182 * (year - 2016) ** 0.5) - 1005
    return cost.astype('float')


def grid_invest_cost(distance):
    cost = 900 * distance + 12500
    return cost


def discount_factor(discount_rate, period):
    dcf_numerator = 1 - (1 + discount_rate) ** (-period)
    dcf_denominator = 1 - (1 + discount_rate) ** (-1)
    dcf = dcf_numerator / dcf_denominator
    return dcf


def levelized_cost(capacity_factor, availability, overnight_cost, grid_cost, fix_om, var_om, discount_rate, lifetime):
    """
    Calculates wind turbines' levelized cost of electricity in EUR per MWh
    :param capacity_factor: xarray DataArray
    :param overnight_cost: in EUR/MW
    :param grid_cost: xarray DataArray
    :param fix_om: EUR/MW
    :param var_om: EUR/MWh
    :param discount_rate: percent
    :param lifetime: years
    :return:
    """
    npv_energy = capacity_factor * availability * 8760 * discount_factor(discount_rate, lifetime)

    npv_cost = capacity_factor.copy()
    npv_cost = npv_cost.where(npv_cost.isnull(), (var_om * capacity_factor * 8760 + fix_om) * discount_factor(discount_rate, lifetime))
    npv_cost = npv_cost + overnight_cost + grid_cost
    lcoe = npv_cost / npv_energy
    return lcoe


# %% define functions
def kdnearest(gdfA, gdfB, gdfB_cols=['Place']):
    # resetting the index of gdfA and gdfB here.
    gdfA = gdfA.reset_index(drop=True)
    gdfB = gdfB.reset_index(drop=True)
    # original code snippet from https://gis.stackexchange.com/questions/222315/finding-nearest-point-in-other-geodataframe-using-geopandas/301935#301935
    A = np.concatenate(
        [np.array(geom.coords) for geom in gdfA.geometry.to_list()])
    B = [np.array(geom.coords) for geom in gdfB.geometry.to_list()]
    B_ix = tuple(itertools.chain.from_iterable(
        [itertools.repeat(i, x) for i, x in enumerate(list(map(len, B)))]))
    B = np.concatenate(B)
    kd_tree = KDTree(B)
    dist, idx = kd_tree.query(A, k=1)
    idx = itemgetter(*idx)(B_ix)
    gdf = pd.concat(
        [gdfA, gdfB.loc[idx, gdfB_cols].reset_index(drop=True),
         pd.Series(dist, name='dist')], axis=1)
    return gdf


def splitlines(lines, num_splits):
    sublines = []
    for i in range(len(lines)):
        for n in range(num_splits):
            sublines.append(substring(lines.iloc[i].geometry,
                                      (n/num_splits)*lines.iloc[i].geometry.length,
                                      ((n+1)/num_splits)*lines.iloc[i].geometry.length))
    linegdf = gpd.GeoDataFrame(geometry=sublines)
    return linegdf


def segments(curve):
    lstlst = []
    curve = curve.reset_index(drop=True)
    for k in range(len(curve)):
        lst = list(map(LineString, zip(curve[k].coords[:-1], curve[k].coords[1:])))
        lstlst.extend(lst)
    return lstlst


def sliced_location_optimization(gams_dict, gams_transfer_container, lcoe_array, num_slices, num_turbines, space_px,
                                 gdx_out_string='base', read_only=False, axis=0):

    locations = pd.DataFrame()
    lcoe_df = pd.DataFrame(data=lcoe_array.data)
    num_pixels = np.ceil(np.round(lcoe_array.count().data, 0) / (num_slices))
    os.chdir(gams_dict['gdx_output'])
    if axis == 0:
        dim_max = lcoe_array.sizes['x']
    elif axis == 1:
        dim_max = lcoe_array.sizes['y']
    else:
        raise ValueError('axis must be 0 or 1')
    j = 0
    i = 0
    for n in range(0, num_slices):
        size = 0
        while size <= num_pixels and i < dim_max:
            if axis == 0:
                lcoe_slice = lcoe_df.iloc[:, i]
            elif axis == 1:
                lcoe_slice = lcoe_df.iloc[i, :]
            else:
                raise ValueError('Only 2-dimensional arrays allowed')
            lcoe_slice = lcoe_slice.dropna()
            i += 1
            size = size + len(lcoe_slice)

        if axis == 0:
            lcoe_map = lcoe_df.iloc[:, j:i]
        else:
            lcoe_map = lcoe_df.iloc[j:i, :]

        gdx_out = gams_dict['gdx_output'] / f'locations_{gdx_out_string}_{n}.gdx'
        if not read_only:
            gams_transfer_container.removeSymbols(['l', 'b', 'i', 'j', 'lcoe', 'num_turbines'])
            laenge = gams_transfer_container.addSet('l', records=list(lcoe_map.index), description='laenge')
            breite = gams_transfer_container.addSet('b', records=list(lcoe_map.columns), description='breite')
            abstd_l = gams_transfer_container.addSet('i', records=list(range(0, space_px)), description='abstand in laenge')
            abstd_b = gams_transfer_container.addSet('j', records=list(range(0, space_px)), description='abstand in  breite')
            gams_transfer_container.addParameter('lcoe', domain=[laenge, breite],
                                                                  records=lcoe_map.stack().reset_index())
            gams_transfer_container.addParameter('num_turbines', domain=[], records=num_turbines)
            gams_transfer_container.write(str(gams_dict['gdx_input']))
            # run optimization
            gms_exe_dir = gams_dict['gams_exe']
            gms_model = gams_dict['gams_model']
            subprocess.run(f'{gms_exe_dir}\\gams {gms_model} gdx={gdx_out} lo=3 o=nul')

        results = gt.Container()
        results.read(str(gdx_out), 'build')
        locs = results.data['build'].records[['l_0', 'b_1', 'level']]
        locs = locs.loc[locs['level'] > 0]
        locations = locations.append(locs)
        # print(f'j: {j}, i: {i}. Using rows {j} to {i} with pixel {num_pixels} of size of {size}')
        j = i
    locations['l_0'] = locations['l_0'].astype('int')
    locations['b_1'] = locations['b_1'].astype('int')
    return locations


def distance_2d(df, dim1, dim2):
    # original code snippet from:
    # https://gis.stackexchange.com/questions/222315/finding-nearest-point-in-other-geodataframe-using-geopandas/301935#301935
    A = df[[dim1, dim2]].values  # np.concatenate([np.array(geom.coords) for geom in gdfA.geometry.to_list()])
    kd_tree = KDTree(A)
    dist, idx = kd_tree.query(A, k=2)
    return dist, idx


def locations_to_gdf(location_array, locations):
    lcoe_gdf = location_array[locations['l_0'], locations['b_1']]
    lcoe_gdf = gpd.GeoDataFrame(data=lcoe_gdf.data.diagonal(), columns=['LCOE'],
                                geometry=gpd.points_from_xy(lcoe_gdf.x, lcoe_gdf.y), crs=lcoe_gdf.rio.crs)
    lcoe_gdf = lcoe_gdf.sort_values(by='LCOE')
    lcoe_gdf.reset_index(inplace=True, drop=True)
    return lcoe_gdf
