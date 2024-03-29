# %% imports
from pathlib import Path


# %% global settings
where = 'home'
if where == 'home':
    ROOTDIR = Path('c:/git_repos/impax')
else:
    ROOTDIR = Path('d:/git_repos/boud')

country = 'AUT'

# turbines to consider
turbines = {
#    'Dewind.D6.1250': [1250, 92, 64, 2003],  # 'Dewind.D6.1250'
#    'Dewind.D8.2000': [2000, 100, 80, 2003],  # NA
    'Enercon.E101.3050': [3050, 135, 101, 2014],
#    'Enercon.E115.3000': [3000, 135, 115, 2016],
#    'Enercon.E126.7500': [7500, 138, 126, 2012],
#    'Enercon.E40.500': [500, 50, 40, 1998],  # 'Enercon.E40 5.40.500'
    # 'Enercon.E40 a.500': 65,
#    'Enercon.E40.600': [600, 65, 40, 2002],  # 'Enercon.E40 6.44.600'
#    'Enercon.E66.1800': [1800, 85, 66, 2003],  # 'Enercon.E66 18.70.1800'
#    'Enercon.E66.2000': [2000, 98, 66, 2004],  # 'Enercon.E66 20.70.2000'
#    'Enercon.E70.1800': [1800, 86, 70, 2006],
#    'Enercon.E70.2000': [2000, 86, 70, 2006],  # 'Enercon.E70 E4.2000'
#    'Enercon.E70.2300': [2300, 113, 70, 2012],
#    'Enercon.E82.2300': [2300, 108, 82, 2012],  # 'Enercon.E82 E2.2300'
#    'Enercon.E82.3000': [3000, 78, 82, 2016],  # 'Enercon.E82 E2.3000'
#    'Enercon.E92.2350': [2350, 104, 92, 2015],
#    'GE.1.5sl': [1500, 85, 77, 2004],  # 'GE.1.5sl.1500'
    # #'NEG.Micon.750.750': 70,
    # #'NEG.Micon.1500.1500': 60,
#    'Nordex.N29.250': [250, 50, 30, 1996],
    # # 'Repower.3XM.3200': 128, REpower.3.4M
#    'Repower.M114.3000': [3000, 143, 114, 2013],
#    'REpower.MM82.2000': [2000, 100, 82, 2005],
#    'REpower.MM92.2000': [2000, 100, 92, 2012],
    # 'Senvion/REpower.S114.3200': 143,  # 'Senvion.3.2M114.3170'
    # #'Siemens.Bonus.1300': 60,
#    'Vestas.V100.1800': [1800, 100, 100, 2012],
#    'Vestas.V100.2000': [2000, 105, 100, 2016],
#    'Vestas.V112.3000': [3000, 120, 112, 2015],
    # 'Vestas.V112 a.3000': 140,
#    'Vestas.V112.3300': [3300, 94, 112, 2016],
#    'Vestas.V112.3450': [3450, 84, 112, 2016],
#    'Vestas.V126.3300': [3300, 137, 126, 2016],
#    'Vestas.V126.3450': [3450, 117, 126, 2016],
#    'Vestas.V44.600': [600, 63, 44, 1997],
#    'Vestas.V47.660': [660, 65, 47, 2000],
#    'Vestas.V80.2000': [2000, 100, 80, 2003],
#    'Vestas.V90.2000': [2000, 105, 90, 2007],
}
