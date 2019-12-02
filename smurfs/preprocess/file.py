import os
import numpy as np
from lightkurve import LightCurve
from smurfs.preprocess.tess import mag
from smurfs.support.mprint import *

def load_file(file : str) -> LightCurve:
    """
    Loads and normalizes target content
    :param file: Name of target including path
    :return: LightCurve object
    """
    if not os.path.exists(file):
        raise IOError(ctext(f"File {file} doesn't exist!",error))

    mprint(f"Reading data from {file} ...",log)
    data = np.loadtxt(file)
    if data.shape[0] > data.shape[1]:
        data = data.T

    if data.shape[0] == 2:
        lc = LightCurve(time=data[0],flux=data[1])
    else:
        lc = LightCurve(time=data[0], flux=data[1],flux_err=data[2])

    lc = lc.remove_nans()
    lc.flux = lc.flux + float(np.amin(lc.flux)) + 10
    lc = mag(lc)
    lc = lc.remove_outliers(4)
    lc = lc.remove_nans()
    mprint(f"Total observation length: {'%.2f' % (lc.time[-1] - lc.time[0])} days.",log)
    mprint("Extracted data from target!",info)
    return lc