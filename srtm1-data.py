
import os
from srtm import Srtm1HeightMapCollection
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

os.putenv('SRTM1_DIR', 'N37W123.hgt')
srtm1_data = Srtm1HeightMapCollection()
prof = srtm1_data.get_points(37.715260765505214, -122.50787498340325, 37.80632767073778, -122.39383891323534)
print(list(prof))
