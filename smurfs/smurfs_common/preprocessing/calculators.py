import numpy as np
from uncertainties import unumpy as unp
import astropy.units as u

from smurfs.smurfs_common.signal.lightcurve import LightCurve


def mag(lc: LightCurve) -> LightCurve:
    """
    Converts and normalizes a LightCurve object to magnitudes.

    :param lc: lightcurve object
    :return: reduced light curve object
    """
    lc = lc.remove_nans()

    flux = lc.flux.value
    flux = flux + (np.abs(2 * np.amin(flux)) if np.amin(flux) < 0 else 100)
    flux = unp.uarray(flux, np.abs(lc.flux_err.value))

    flux = -2.5 * unp.log10(flux)

    valid_flux = flux[~np.isnan(unp.nominal_values(flux))]
    valid_flux -= np.median(unp.nominal_values(valid_flux))

    lc.flux = unp.nominal_values(valid_flux) * u.mag
    lc.flux_err = unp.std_devs(valid_flux) * u.mag
    return lc