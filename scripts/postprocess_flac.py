# %% imports
import pandas as pd
import xarray as xr

from config import ROOTDIR

# %% read flac prediction
fpd = pd.read_csv(ROOTDIR / 'data/flac_prediction.csv')
fpd.index = pd.MultiIndex.from_arrays([fpd['y'], fpd['x']])
fpd = fpd['predict']
far = fpd.to_xarray()

far.plot(robust=True)
plt.show()