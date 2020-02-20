from lightkurve import search_lightcurvefile, TessLightCurveFile, LightCurveCollection
import lightkurve as lk
from typing import List, Tuple, Union
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
from astroquery.mast import Catalogs
from astroquery.mast import Observations
import astropy.units as u
from matplotlib import rcParams
import warnings
from smurfs.signal.lightcurve import LightCurve
from eleanor.visualize import Visualize

params = {
    'axes.labelsize': 16,
    #   'text.fontsize': 8,
    'legend.fontsize': 18,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'text.usetex': False,
    'figure.figsize': [4.5, 4.5]
}
rcParams.update(params)


def aperture_contour(ax: Axes, obj: eleanor.TargetData):
    """
    Plots a countour plot of the TPF with the aperture by Eleanor.

    :param ax: Axes object where this is plotted on
    :param obj: TargetData object containing TPF
    :return: used axes object
    """
    aperture = obj.aperture

    ax.imshow(obj.tpf[0],cmap='binary')

    f = lambda x, y: aperture[int(y), int(x)]
    g = np.vectorize(f)

    x = np.linspace(0, aperture.shape[1], aperture.shape[1] * 100)
    y = np.linspace(0, aperture.shape[0], aperture.shape[0] * 100)
    X, Y = np.meshgrid(x[:-1], y[:-1])
    Z = g(X[:-1], Y[:-1])

    ax.contour(Z[:-1], [0.5], colors='r', linewidths=[4],
               extent=[0 - 0.5, x[:-1].max() - 0.5, 0 - 0.5, y[:-1].max() - 0.5])


def create_validation_page(data_list: List[eleanor.TargetData], q_list: List[np.ndarray],
                           title: str,do_psf = False, do_pca = False,flux_type : str = "PDCSAP") -> List[Figure]:

    fig_main: Figure = pl.figure(figsize=(11.69,8.27),dpi=100)
    ax : Axes= fig_main.add_subplot()

    for data, q in zip(data_list, q_list):
        if flux_type == 'PDCSAP':
            ax.plot(data.time[q], data.pca_flux[q] - np.median(data.pca_flux[q]), '.', markersize=2,
                    label=f"Sector {data.source_info.sector}")
        elif flux_type == 'PSF':
            ax.plot(data.time[q], data.psf_flux[q] - np.median(data.psf_flux[q]), '.', markersize=2,
                    label=f"Sector {data.source_info.sector}")
        else:
            ax.plot(data.time[q], data.corr_flux[q] - np.median(data.corr_flux[q]), '.', markersize=2,
                    label=f"Sector {data.source_info.sector}")
    ax.legend()
    ax.set_xlabel("Time")
    ax.set_ylabel("Flux")
    fig_main.suptitle(f"{title} - extracted light curve, flux type: {flux_type}")
    pl.tight_layout()

    reduction_figs = []

    for i, (data, q) in enumerate(zip(data_list, q_list)):
        fig : Figure= pl.figure(figsize=(8.27,11.69),dpi=100)
        gs = GridSpec(3,3, width_ratios=[1, 1, 1], height_ratios=[3,3,2])

        ax: Axes = fig.add_subplot(gs[0, 0:])

        ax.plot(data.time[q], data.raw_flux[q]/np.nanmedian(data.raw_flux[q])+0.2, 'ok',label='Raw flux',markersize=1)
        ax.plot(data.time[q], data.corr_flux[q]/np.nanmedian(data.corr_flux[q]) + 0.1, 'or',label='Corrected flux',markersize=1)
        if do_pca:
            ax.plot(data.time[q], data.pca_flux[q]/np.nanmedian(data.pca_flux[q]), 'og',label='PCA flux',markersize=1) #aperture × TPF + background subtraction + cotrending basis vectors
        if do_psf:
            ax.plot(data.time[q], data.psf_flux[q]/np.nanmedian(data.psf_flux[q]) - 0.1, 'ob',label='PSF modelled flux',markersize=1)
        ax.legend()

        ax: Axes = fig.add_subplot(gs[1, 0:])
        ax.plot(data.time, data.flux_bkg, 'k', label='1D postcard', linewidth=2)
        ax.plot(data.time, data.tpf_flux_bkg, 'r--', label='1D TPF', linewidth=1)
        ax.legend()
        ax.set_title("Background flux")

        ax: Axes = fig.add_subplot(gs[2, 0])
        aperture_contour(ax, data)
        ax.set_title("TPF with aperture")
        ax.set_xticks([])
        ax.set_yticks([])

        ax: Axes = fig.add_subplot(gs[2, 1])
        tpf_data = data.tpf[0]
        tpf_data[data.aperture != 1] = 0
        ax.imshow(tpf_data,cmap='binary')
        ax.set_title("Aperture content")
        ax.set_yticks([])
        ax.set_xticks([])

        ax: Axes = fig.add_subplot(gs[2, 2])
        ax.imshow(data.bkg_tpf[0],cmap='binary')
        ax.set_title("Interpolated background")
        ax.set_yticks([])
        ax.set_xticks([])

        fig.suptitle(f"{title} - Sector {data.source_info.sector}")
        pl.tight_layout()

        reduction_figs.append(fig)

    return  [fig_main] + reduction_figs


from uncertainties import unumpy as unp, ufloat


def mag(lc: LightCurve) -> LightCurve:
    """
    Converts and normalizes a LighCurve object to magnitudes.

    :param lc: lightcurve object
    :return: reduced light curve object
    """

    lc = lc.remove_nans()

    flux = lc.flux + (np.abs(2 * np.amin(lc.flux)) if np.amin(lc.flux) < 0 else 100)
    flux = unp.uarray(flux, lc.flux_err)
    flux = -2.5 * unp.log10(flux)
    flux = flux[~unp.isnan(flux)]
    flux -= np.median(flux)

    lc.flux = unp.nominal_values(flux) * u.mag
    lc.flux_err = unp.std_devs(flux) * u.mag
    return lc


def cut_ffi(tic_id:int,clip :float = 4,iter : int = 1,do_pca : bool = False, do_psf :bool = False,flux_type = 'PDCSAP') -> Tuple[LightCurve, List[Figure]]:
    """
    Extracts light curves from FFIs using TESScut and Eleanor. This function automatically combines all available
    sectors for a given target.

    :param tic_id: TIC ID of the target
    :param clip: Sigma clip range of the target.
    :param iter: Iterations of the sigma clipping
    :param do_pca: Perform pca analysis with eleanor
    :param do_psf: Perform psf analysis with eleanor
    :param flux_type: Flux type that is returned. Choose between 'PDCSAP','SAP','PSF'
    :return: Lightcurve
    """
    flux_types = ['SAP','PDCSAP', 'PSF']
    if flux_type not in flux_types:
        raise ValueError(mprint(f"Flux type {flux_type} not recognized. Possible values are: {flux_types}",error))
    f = io.StringIO()
    with redirect_stdout(f):
        stars = eleanor.multi_sectors(tic=tic_id, sectors='all',tc=True)
    mprint(f.getvalue().strip(), log)

    lc_list = []
    data_list = []
    q_list = []

    pca_flag = do_pca or flux_type == 'PDCSAP'
    psf_flag = do_psf or flux_type == 'PSF'

    for star in stars:

        f = io.StringIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            data = eleanor.TargetData(star, height=15, width=15, bkg_size=31, do_pca=pca_flag, do_psf=psf_flag)
        mprint(f.getvalue().strip(), log)
        q = data.quality == 0
        if flux_type == 'SAP':
            lc_list.append(LightCurve(lk.TessLightCurve(time=data.time[q], flux=data.corr_flux[q], targetid=tic_id)))
        elif flux_type == 'PDCSAP':
            lc_list.append(LightCurve(lk.TessLightCurve(time=data.time[q], flux=data.pca_flux[q], targetid=tic_id)))
        else:
            lc_list.append(LightCurve(lk.TessLightCurve(time=data.time[q], flux=data.psf_flux[q], targetid=tic_id)))

        data_list.append(data)
        q_list.append(q)

    fig = create_validation_page(data_list, q_list, f'TIC {tic_id}',do_pca=pca_flag,do_psf=psf_flag,flux_type=flux_type)

    lc : LightCurve = combine_light_curves(lc_list,clip,iter)
    mprint(f"Extracted light curve for TIC {tic_id}!", info)
    return lc, fig

def combine_light_curves(target_list: List[Union[lk.TessLightCurve, lk.KeplerLightCurve]],sigma_clip :float = 4,iters : int = 1) -> LightCurve:
    kepler_collection = LightCurveCollection([i for i in target_list if isinstance(i, lk.KeplerLightCurve)])
    tess_collection = LightCurveCollection([i for i in target_list if isinstance(i, lk.TessLightCurve)])

    if len(kepler_collection) != 0 and len(tess_collection) != 0:
        kepler_lc: lk.KeplerLightCurve = kepler_collection.stitch(corrector_func=mag)
        tess_lc: lk.TessLightCurve = tess_collection.stitch(corrector_func=mag)

        return LightCurve(kepler_lc.remove_nans().remove_outliers(sigma_clip,maxiters=iters).append(tess_lc.remove_nans().remove_outliers(4,maxiters=1)))
    elif len(kepler_collection) != 0:
        return LightCurve(kepler_collection.stitch(corrector_func=mag).remove_nans().remove_outliers(sigma_clip,maxiters=iters))
    elif len(tess_collection) != 0:
        return LightCurve(tess_collection.stitch(corrector_func=mag).remove_nans().remove_outliers(sigma_clip,maxiters=iters))
    else:
        raise ValueError(ctext("No light curves available for target!",error))


def download_lc(target_name: str, flux_type='PDCSAP', mission: str = 'TESS',sigma_clip=4,iters=1,do_pca : bool = False,do_psf :bool= False) -> Tuple[
    LightCurve, Union[List[Figure],None]]:
    """
    Downloads a light curve using the TESS mission. If the star has been observed in the SC mode, it
    will download the original light curve from MAST. You can also choose the flux type you want to use.

    If it wasn't observed in SC mode, it will try to extract a light curve from the FFIs if the target has
    been observed by TESS.

    You can also download light curves of stars that are observed by the K2 or Kepler mission, by setting
    the mission parameter.

    :param target_name: Name of the target. You can either provide the TIC ID (TIC ...), Kepler ID (KIC ...), K2 ID(EPIC ...) or a name that is resolvable by Simbad.
    :param flux_type: Type of flux in the SC mode. Can be either PDCSAP or SAP or PSF for long cadence data
    :param mission: Mission from which the light curves are extracted. By default TESS only is used. You can consider all missions by passing 'all' (TESS, Kepler, K2)
    :param sigma_clip: Sigma clip parameter. Defines the number of standard deviations that are clipped.
    :param iters: Iterations for the sigma clipping
    :return: lightkurve.LightCurve object and validation page if extracted from FFI
    """
    chosen_mission = [mission] if mission != 'all' else ('Kepler', 'K2', 'TESS')
    mprint(f"Searching processed light curves for {target_name} on mission(s) {','.join(chosen_mission)} ... ", log)

    if chosen_mission == ['TESS']:
        if target_name.startswith('TIC'):
            tic_id = re.findall(r'\d+', target_name)
            if len(tic_id) == 0:
                raise ValueError(ctext("A Tic ID needs to consist of TIC and a number!", error))
            tic_id = int(tic_id[0])
        else:
            mprint(f"Resolving {target_name} to TIC using MAST ...",log)
            try:
                tic_id = Catalogs.query_object(target_name,catalog='TIC',radius=0.003)[0]['ID']
            except KeyError:
                raise ValueError(ctext(f"No TESS observations available for {target_name}", error))

            mprint(f"TIC ID for {target_name}: TIC {tic_id}",log)

        o = Observations.query_criteria(objectname=target_name, radius=str(0 * u.deg), project='TESS',
                                        obs_collection='TESS').to_pandas()

        if len(o) > 0 and len(o[o.target_name != 'TESS FFI']) > 0:
            mprint(f"Short cadence observations available for {target_name}. Downloading ...",info)
            res = search_lightcurvefile(target_name, mission=chosen_mission)
        else: #Only FFI available
            mprint(f"No short cadence data available for {target_name}, extracting from FFI ...",info)
            lc, fig = cut_ffi(tic_id,sigma_clip,iters,do_pca,do_psf,flux_type)
            mprint(f"Total observation length: {'%.2f' % (lc.time[-1] - lc.time[0])} days.", log)
            return lc, fig
    else:
        res = search_lightcurvefile(target_name, mission=chosen_mission)

    if len(res) != 0:
        fig = None
        mprint(f"Found processed light curve for {target_name}!", info)
        res = res.download_all()
        types = []

        for d in res.data:
            type = 'TESS' if isinstance(d, lk.TessLightCurveFile) else 'Kepler'
            if type not in types:
                types.append(type)

        mprint(f"Using {','.join(types)} observations! Combining sectors ...", log)

        if flux_type == 'PSF':
            mprint(f"PSF not available for short cadence data. Reverting to PDCSAP",warn)
            flux_type = 'PDCSAP'

        if flux_type == 'PDCSAP':
            lc_set: List[Union[lk.TessLightCurve, lk.KeplerLightCurve]] = [i for i in res.PDCSAP_FLUX.data]
        elif flux_type == 'SAP':
            lc_set: List[Union[lk.TessLightCurve, lk.KeplerLightCurve]] = [i for i in res.SAP_FLUX.data]
        else:
            raise ValueError(ctext("Flux type needs to be either PDCSAP or SAP", error))
        lc = combine_light_curves(lc_set,sigma_clip=sigma_clip,iters=iters)
    else:
        raise ValueError(ctext(f"No light curve available for {target_name} on mission(s) {chosen_mission}",error))

    mprint(f"Total observation length: {'%.2f' % (lc.time[-1] - lc.time[0])} days.", log)
    return lc, fig
