import os.path
from enum import Enum
from pathlib import Path

import numpy as np
from pandas import read_csv

from smurfs.preprocessing.calculators import mag
from smurfs.signal.lightcurve import LightCurve
from smurfs.support.mprint import mprint, log, warn, info


class Mission(str, Enum):
    KEPLER = "Kepler"
    TESS = "TESS"
    K2 = "K2"


class FluxType(str, Enum):
    PDCSAP = "PDCSAP"
    SAP = "SAP"
    PSF = "PSF"


def load_data_from_file(target_path : Path, clip: float = 4, it: int = 1, apply_file_correction: bool = False) -> LightCurve:
    if not target_path.exists():
        raise FileNotFoundError(f"File {target_path} doesn't exist!")

    mprint(f"Reading data from {target_path} ...", log)
    try:
        data = np.loadtxt(target_path)
    except ValueError:
        data = read_csv(target_path)
        data = np.array((data.time, data.flux))
    if data.shape[0] > data.shape[1]:
        data = data.T

    if data.shape[0] == 2:
        lc = LightCurve(time=data[0], flux=data[1])
    else:
        lc = LightCurve(time=data[0], flux=data[1], flux_err=data[2])

    lc = lc.remove_nans()
    if apply_file_correction:
        lc.flux = lc.flux + float(np.amin(lc.flux)) + 10
        lc = lc.remove_outliers(clip, maxiters=it)
        lc = mag(lc)
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
    mprint(f"Total observation length: {'%.2f' % (lc.time[-1] - lc.time[0]).value} days.", log)
    mprint("Extracted data from target!", info)
    return lc


def load_data(target_name : str, flux_type: FluxType, mission: Mission = Mission.TESS) -> LightCurve:
    target_path = Path(target_name)

    if target_path.is_file():
        return load_data_from_file(target_path,flux_type)
    else:
        raise FileNotFoundError(f"File {target_path} doesn't exist!")
        #return load_data_from_mission(target_name,flux_type,mission)

    pass