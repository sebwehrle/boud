# %% imports
import shutil
import certifi
import urllib3
import numpy as np
import pandas as pd

from ast import literal_eval
from scipy.interpolate import interp1d


# %% functions
def download_file(url, save_to):
    """
    downloads a file from a specified url to disk
    :param url: url-string
    :param save_to: destination file name (string)
    :return:
    """
    http = urllib3.PoolManager(ca_certs=certifi.where())
    with http.request('GET', url, preload_content=False) as r, open(save_to, 'wb') as out_file:
        shutil.copyfileobj(r, out_file)


def process_power_curves(turbines, renewables_ninja_curves, open_energy_curves):
    u_pwrcrv = np.linspace(0.5, 30, num=60)
    powercurves = pd.DataFrame(index=u_pwrcrv)

    missing_turbs = []
    for turbine, _ in turbines.items():
        if open_energy_curves['type_string'].str.contains(turbine).any():
            sel = open_energy_curves['type_string'].str.contains(turbine)
            n = open_energy_curves[sel].index[0]
            f_itpl = interp1d(literal_eval(open_energy_curves.loc[n, 'power_curve_wind_speeds']),
                              literal_eval(open_energy_curves.loc[n, 'power_curve_values']) / open_energy_curves.loc[
                                  n, 'nominal_power'], kind='linear', bounds_error=False, fill_value=0)
            powercurves[open_energy_curves.loc[n, 'type_string']] = f_itpl(u_pwrcrv)
        elif turbine in renewables_ninja_curves.columns:
            f_itpl = interp1d(renewables_ninja_curves['speed'], renewables_ninja_curves[turbine], kind='linear')
            powercurves[turbine] = f_itpl(u_pwrcrv)
        else:
            missing_turbs.append(turbine)
    powercurves.index.name = 'speed'