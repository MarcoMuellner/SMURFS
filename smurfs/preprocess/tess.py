from lightkurve import search_lightcurvefile, TessLightCurve, TessLightCurveFile
from typing import List,Tuple
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import re
import eleanor
from astroquery.mast import Tesscut
from astroquery.mast import Catalogs
import numpy as np
import astropy.units as u
from smurfs.support.mprint import *
from contextlib import redirect_stdout
import io
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as pl


def aperture_contour(ax : Axes, obj : eleanor.TargetData) -> Axes:
    """
    Plots a countour plot of the TPF with the aperture by Eleanor.
    :param ax: Axes object where this is plotted on
    :param obj: TargetData object containing TPF
    :return: used axes object
    """
    aperture = obj.aperture

    ax.imshow(obj.tpf[0])

    f = lambda x, y: aperture[int(y), int(x)]
    g = np.vectorize(f)

    x = np.linspace(0, aperture.shape[1], aperture.shape[1] * 100)
    y = np.linspace(0, aperture.shape[0], aperture.shape[0] * 100)
    X, Y = np.meshgrid(x[:-1], y[:-1])
    Z = g(X[:-1], Y[:-1])

    ax.contour(Z[::-1], [0.5], colors='w', linewidths=[4],
                extent=[0 - 0.5, x[:-1].max() - 0.5, 0 - 0.5, y[:-1].max() - 0.5])

def create_validation_page(data_list: List[eleanor.TargetData], q_list: List[np.ndarray],
                           title : str) -> Figure:
    """
    Creates a validation page from the eleanor extraction of light curves from TESS FFIs.
    Contains the pixel cutout, the original and reduced light curve.
    :param data_list: List of tpfs from eleanor
    :param q_list: Quality flag list
    :param title: Title of pplot
    """
    fig: Figure = pl.figure(figsize=(14, 12 + 4 * len(data_list)))
    height_ratio = [2] + [1 for i in range(len(data_list) - 1)] + [1]
    gs = GridSpec(len(data_list) + 1, 4, width_ratios=[1, 1, 1, 1], height_ratios=height_ratio)
    ax: Axes = fig.add_subplot(gs[0, :])

    for data, q in zip(data_list, q_list):
        ax.plot(data.time[q], data.corr_flux[q] - np.median(data.corr_flux[q]), '.', markersize=2,
                label=f"Sector {data.source_info.sector}")
    ax.legend()
    ax.set_xlabel("Time")
    ax.set_ylabel("Flux")

    for i, (data, q) in enumerate(zip(data_list, q_list)):
        ax: Axes = fig.add_subplot(gs[i + 1, 0])
        aperture_contour(ax, data)
        ax.set_title("TPF with aperture")

        ax: Axes = fig.add_subplot(gs[i + 1, 1:])
        ax.plot(data.time[q],
                data.raw_flux[q] / np.median(data.raw_flux[q]) - 0.01, 'k.',
                label='Raw flux')
        ax.plot(data.time[q],
                data.corr_flux[q] / np.median(data.corr_flux[q]) + 0.01, 'r.',
                label='Corrected flux')
        ax.legend()

        ax.set_title(f"Sector {data.source_info.sector}")

    fig.suptitle(f"{title}")
    fig.subplots_adjust(hspace=0.3)

    return fig


def mag(lc: TessLightCurve) -> TessLightCurve:
    """
    Converts and normalizes a LighCurve object to magnitudes.
    :param lc: lightcurve object
    :return: reduced light curve object
    """
    lc = lc.remove_nans()
    error = lc.flux_err/lc.flux
    lc.flux = -2.5 * np.log10(lc.flux)
    lc = lc.remove_nans()
    lc.flux -= np.median(lc.flux)
    lc.flux = lc.flux * u.mag
    lc.flux_err = lc.flux*error
    return lc


def cut_ffi(tic_id: int) -> Tuple[TessLightCurve,Figure]:
    """
    Extracts light curves from FFIs using TESScut and Eleanor. Querying all available sectors for a given TIC ID.
    :param tic_id: ID of the star in the TIC
    :return: Tess light curve and figure containing validation page
    """
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            stars = eleanor.multi_sectors(tic=tic_id, sectors='all')
        except:
            stars = eleanor.multi_sectors(tic=tic_id, sectors='all', tc=True)
    mprint(f.getvalue().strip(), log)

    lc_list = []
    data_list = []
    q_list = []

    for star in stars:
        data = eleanor.TargetData(star, height=15, width=15, bkg_size=31, do_psf=False, do_pca=False)
        q = data.quality == 0
        lc_list.append(TessLightCurve(time=data.time[q], flux=data.corr_flux[q], targetid=tic_id))

        data_list.append(data)
        q_list.append(q)

    fig = create_validation_page(data_list,q_list,f'TIC {tic_id}')

    lc: TessLightCurve = lc_list[0]
    lc = mag(lc)
    if len(lc_list) > 1:
        for l in lc_list:
            lc = lc.append(mag(l))
    mprint(f"Extracted light curve for TIC {tic_id}!", info)
    return lc, fig


def get_tess_ffi_lc(target_name: str) -> Tuple[TessLightCurve,Figure]:
    """
    Tries to extract a light curve from TESS FFIs. If you do not provide a TIC number, it will try
    to look up the target on Simbad and link it to the TESS catalog using Simbad.
    :param target_name: Name of the target. It is recommended to use the TIC ID directly, if you provide
    any other name, it needs to be able to be looked up in Simbad. It then links the target by the coordinates
    from Simbad to the TIC catalogue.
    :return: A TessLightCurve object containing the Light curve of the object, validation page figure
    """
    if target_name.startswith('TIC'):
        tic_id = re.findall(r'\d+', target_name)
        if len(tic_id) == 0:
            raise ValueError(ctext("A Tic ID needs to consist of TIC and a number!", error))
        tic_id = int(tic_id[0])
    else:
        mprint(f"Querying simbad for {target_name}", log)

        simbad_query = Simbad.query_object(target_name)
        if simbad_query is None:
            raise ValueError(ctext(f"Can't find a simbad entry for {target_name}", error))

        c = SkyCoord(simbad_query[0]['RA'] + " " + simbad_query[0]['DEC'], unit=(u.hourangle, u.deg))
        mprint(f"Found {target_name} at {c}. Searching for TESS observations using TESScut ...", info)

        hdulist = Tesscut.get_sectors(coordinates=c)
        if len(hdulist) == 0:
            raise ValueError(ctext(f"Can't find a TESS observation for {target_name}", error))
        try:
            tic_star = Catalogs.query_region(f"{c.ra} {c.dec}", radius=0.0001, catalog="TIC")
        except:
            tic_star = Catalogs.query_region(f"{c.ra.value} {c.dec.value}", radius=0.0001, catalog="TIC")

        if len(tic_star) > 1:
            raise RuntimeWarning(ctext("Found two stars in the coordinates of this star!", error))

        tic_star = tic_star[0]
        tic_id = tic_star['ID']
        mprint(f"Found TESS observations for {target_name} with TIC {tic_id}", info)

    mprint(f"Extracting light curves from FFIs, this may take a bit ... ", log)
    return cut_ffi(tic_id)


def download_lc(target_name: str, flux_type='PDCSAP') -> Tuple[TessLightCurve,Figure]:
    """
    Downloads a light curve using the TESS mission. If the star has been observed in the SC mode, it
    will download the original light curve from MAST. You can also choose the flux type you want to use.

    If it wasn't observed in SC mode, it will try to extract a light curve from the FFIs if the target has
    been observed by TESS.
    :param target_name: The name of the target. It is recommended to use the TIC ID directly, if you provide
    any other name, it needs to be able to be looked up in Simbad. It then links the target by the coordinates
    from Simbad to the TIC catalogue.
    :param flux_type: Type of flux in the SC mode. Can be either PDCSAP or SAP
    :return: A TessLightCurve object containing the Light curve of the objectl, validation page if
    extracted from FFI
    """
    mprint(f'Searching processed light curves for {target_name} ...', log)
    res = search_lightcurvefile(target_name)
    if len(res) == 0:
        mprint(f'No light curve found using light kurve. Checking TESS FFIs ...', log)
        lc,fig = get_tess_ffi_lc(target_name)
    else:
        fig = None
        mprint(f"Found processed light curve for {target_name}!", info)
        res = res.download_all()
        type = 'TESS' if isinstance(res.data[0], TessLightCurveFile) else 'Kepler'
        mprint(f"Using {type} observations! Combining sectors ...", log)

        if flux_type == 'PDCSAP':
            lc: TessLightCurve = res.PDCSAP_FLUX.data[0]
        elif flux_type == 'SAP':
            lc: TessLightCurve = res.SAP_FLUX.data[0]
        else:
            raise ValueError(ctext("Flux type needs to be either PDCSAP or SAP", error))

        lc = mag(lc)
        if len(res) > 1:
            data: List[TessLightCurve] = res.PDCSAP_FLUX.data[1:] if flux_type == 'PDCSAP' else res.SAP_FLUX.data[1:]
            for d in data:
                lc = lc.append(mag(d))

    lc = lc.remove_nans()
    lc = lc.remove_outliers(4)
    mprint(f"Total observation length: {'%.2f' % (lc.time[-1] - lc.time[0])} days.", log)
    return lc,fig
