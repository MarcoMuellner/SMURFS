import os
import numpy as np
from lightkurve import LightCurve
from smurfs.preprocess.tess import mag
from smurfs.support.mprint import *
from pandas import read_csv


def load_file(file: str, clip: float = 4, it: int = 1, apply_file_correction: bool = False) -> LightCurve:
    """
    Loads and normalizes target content
    :param file: Name of target including path
    :return: LightCurve object
    """
    if not os.path.exists(file):
        raise IOError(ctext(f"File {file} doesn't exist!", error))

    mprint(f"Reading data from {file} ...", log)
    try:
        data = np.loadtxt(file)
    except ValueError:
        data = read_csv(file)
        data = np.array((data.time,data.flux))
    if data.shape[0] > data.shape[1]:
        data = data.T

    if data.shape[0] == 2:
        lc = LightCurve(time=data[0], flux=data[1])
    else:
        lc = LightCurve(time=data[0], flux=data[1], flux_err=data[2])

    lc = lc.remove_nans()
    if apply_file_correction:
        lc.flux = lc.flux + float(np.amin(lc.flux)) + 10
        lc = mag(lc)
        lc = lc.remove_outliers(clip, maxiters=it)
        lc = lc.remove_nans()
    else:
        if np.amax(np.abs(lc.flux)) > 10:
            mprint(
                f"It seems as if your flux isn't in magnitudes. Be aware, that SMURFS expects the flux in magnitudes. "
                f"Continuing ...",
                warn)
        if np.abs(np.median(lc.flux)) > 1:
            mprint(
                f"The median of your flux is {'%.2f' % np.median(lc.flux)}. To do a proper analysis, the median should "
                f"be close to 0. Be aware, that this might cause issues. Continuing...",
                warn)
    mprint(f"Total observation length: {'%.2f' % (lc.time[-1] - lc.time[0])} days.", log)
    mprint("Extracted data from target!", info)
    return lc
