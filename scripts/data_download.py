# %% imports
from pathlib import Path
import urllib.request

ROOTDIR = Path('c:/git_repos/impax')

# %% get global wind atlas
country = ['AUT']
layer = ['air-density', 'combined-Weibull-A', 'combined-Weibull-k', 'elevation_w_bathymetry']
height = ['50', '100', '150']

for c in country:
    for l in layer:
        if l == 'elevation_w_bathymetry':
            urlstr = f'https://globalwindatlas.info/api/gis/country/{c}/{l}'
            fname = f'{c}_{l}.tif'
            urllib.request.urlretrieve(urlstr, ROOTDIR / 'data/gwa3' / fname)
        else:
            for h in height:
                urlstr = f'https://globalwindatlas.info/api/gis/country/{c}/{l}/{h}'
                fname = f'{c}_{l}_{h}.tif'
                urllib.request.urlretrieve(urlstr, ROOTDIR / 'data/gwa3' / fname)

# %% get powercurves from rnj and https://openenergy-platform.org/dataedit/view/supply/wind_turbine_library


# %% get borders

# %% get corine land cover
