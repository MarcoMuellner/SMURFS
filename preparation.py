import numpy as np
import scipy
import os

def prepareData(file):
    if not os.path.exists(file):
        raise IOError("File " + file + " doesnt exist!")

    data = np.loadtxt(file).T
    data[0] = data[0]-data[0][0]
    return data