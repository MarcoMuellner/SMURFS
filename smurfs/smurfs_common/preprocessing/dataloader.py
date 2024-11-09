import os.path
from enum import Enum
from pathlib import Path

import numpy as np
from lightkurve import LightCurveCollection
from pandas import read_csv
import lightkurve as lk

from smurfs.smurfs_common.preprocessing.calculators import mag
from smurfs.smurfs_common.signal.lightcurve import LightCurve
from smurfs.smurfs_common.support.mprint import mprint, log, warn, info


class Mission(str, Enum):
    KEPLER = "Kepler"
    TESS = "TESS"
    K2 = "K2"
    all = "all"


class FluxType(str, Enum):
    PDCSAP = "PDCSAP"
    SAP = "SAP"


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

def load_data_from_target_name(target_name : str, flux_type: FluxType, mission: Mission = Mission.TESS, sigma_clip : float =4, iters: int = 1 ) -> LightCurve:

    chosen_mission = (mission,) if mission != Mission.all else (Mission.KEPLER, Mission.TESS, Mission.K2)
    mprint(f"Searching processed light curves for {target_name} on mission(s) {','.join(chosen_mission)} ... ", log)

    if len(chosen_mission) == 1:
        results = lk.search_lightcurve(target_name, mission=chosen_mission[0].value)
    else:
        results = lk.search_lightcurve(target_name)

    if len(results) == 0:
        raise FileNotFoundError(f"No light curve found for {target_name} on mission(s) {','.join(chosen_mission)}")

    downloads = results.download_all()

    available_missions = set([result.mission[0].split(" ")[0] for result in results])
    mprint(f"Found light curves for {target_name} on mission(s) {','.join(available_missions)}", info)

    return LightCurve(downloads.stitch(corrector_func=mag).remove_nans().remove_outliers(sigma_clip,maxiters=iters))

def load_data(target_name : str,  flux_type: FluxType,clip: float = 4, iters: int = 1, mission: Mission = Mission.TESS) -> LightCurve:
    target_path = Path(target_name)

    if target_path.is_file():
        return load_data_from_file(target_path,clip)
    else:
        return load_data_from_target_name(target_name,flux_type,mission, clip, iters)

    pass