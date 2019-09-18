from lightkurve import search_lightcurvefile,TessLightCurve,TessLightCurveFile
from typing import List
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

def mag(lc : TessLightCurve) -> TessLightCurve:
    """
    Converts and normalizes a LighCurve object to magnitudes.
    :param lc: lightcurve object
    :return: reduced light curve object
    """
    lc = lc.remove_nans()
    lc.flux = -2.5 * np.log10(lc.flux)
    lc = lc.remove_nans()
    lc.flux -= np.median(lc.flux)
    lc.flux = lc.flux*u.mag
    return lc

def cut_ffi(tic_id : int) -> TessLightCurve:
    """
    Extracts light curves from FFIs using TESScut and Eleanor. Querying all available sectors for a given TIC ID.
    :param tic_id: ID of the star in the TIC
    :return: Tess light curve
    """
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            stars = eleanor.multi_sectors(tic=tic_id,sectors='all')
        except:
            stars = eleanor.multi_sectors(tic=tic_id, sectors='all',tc=True)
    mprint(f.getvalue().strip(),log)
    lc_list = []

    for star in stars:
        data = eleanor.TargetData(star,height=15,width=15,bkg_size=31,do_psf=False,do_pca=False)
        q = data.quality == 0
        lc_list.append(TessLightCurve(time=data.time[q],flux=data.corr_flux[q],targetid=tic_id))

    lc : TessLightCurve= lc_list[0]
    lc = mag(lc)
    if len(lc_list) > 1:
        for l in lc_list:
            lc = lc.append(mag(l))
    mprint(f"Extracted light curve for TIC {tic_id}!",info)
    return lc


def get_tess_ffi_lc(target_name : str) -> TessLightCurve:
    """
    Tries to extract a light curve from TESS FFIs. If you do not provide a TIC number, it will try
    to look up the target on Simbad and link it to the TESS catalog using Simbad.
    :param target_name: Name of the target. It is recommended to use the TIC ID directly, if you provide
    any other name, it needs to be able to be looked up in Simbad. It then links the target by the coordinates
    from Simbad to the TIC catalogue.
    :return: A TessLightCurve object containing the Light curve of the object
    """
    if target_name.startswith('TIC'):
        tic_id = re.findall(r'\d+',target_name)
        if len(tic_id) == 0:
            raise ValueError(ctext("A Tic ID needs to consist of TIC and a number!",error))
        tic_id = int(tic_id[0])
    else:
        mprint(f"Querying simbad for {target_name}",log)

        simbad_query = Simbad.query_object(target_name)
        if simbad_query is None:
            raise ValueError(ctext(f"Can't find a simbad entry for {target_name}",error))

        c = SkyCoord(simbad_query[0]['RA'] + " " + simbad_query[0]['DEC'], unit=(u.hourangle, u.deg))
        mprint(f"Found {target_name} at {c}. Searching for TESS observations using TESScut ...",info)

        hdulist = Tesscut.get_sectors(coordinates=c)
        if len(hdulist) == 0:
            raise ValueError(ctext(f"Can't find a TESS observation for {target_name}",error))

        tic_star = Catalogs.query_region(f"{c.ra} {c.dec}", radius=0.0001, catalog="TIC")

        if len(tic_star) > 1:
            raise RuntimeWarning(ctext("Found two stars in the coordinates of this star!",error))

        tic_star = tic_star[0]
        tic_id = tic_star['ID']
        mprint(f"Found TESS observations for {target_name} with TIC {tic_id}",info)

    mprint(f"Extracting light curves from FFIs, this may take a bit ... ",log)
    return cut_ffi(tic_id)

def download_lc(target_name : str,flux_type = 'PDCSAP') -> TessLightCurve:
    """
    Downloads a light curve using the TESS mission. If the star has been observed in the SC mode, it
    will download the original light curve from MAST. You can also choose the flux type you want to use.

    If it wasn't observed in SC mode, it will try to extract a light curve from the FFIs if the target has
    been observed by TESS.
    :param target_name: The name of the target. It is recommended to use the TIC ID directly, if you provide
    any other name, it needs to be able to be looked up in Simbad. It then links the target by the coordinates
    from Simbad to the TIC catalogue.
    :param flux_type: Type of flux in the SC mode. Can be either PDCSAP or SAP
    :return: A TessLightCurve object containing the Light curve of the object
    """
    mprint(f'Searching processed light curves for {target_name} ...',log)
    res = search_lightcurvefile(target_name)
    if len(res) == 0:
        mprint(f'No light curve found using light kurve. Checking TESS FFIs ...', log)
        lc =  get_tess_ffi_lc(target_name)
    else:
        mprint(f"Found processed light curve for {target_name}!",info)
        res = res.download_all()
        type = 'TESS' if isinstance(res.data[0],TessLightCurveFile) else 'Kepler'
        mprint(f"Using {type} observations! Combining sectors ...",log)

        if flux_type == 'PDCSAP':
            lc : TessLightCurve= res.PDCSAP_FLUX.data[0]
        elif flux_type == 'SAP':
            lc : TessLightCurve= res.SAP_FLUX.data[0]
        else:
            raise ValueError(ctext("Flux type needs to be either PDCSAP or SAP",error))

        lc = mag(lc)
        if len(res) > 1:
            data  : List[TessLightCurve]= res.PDCSAP_FLUX.data[1:] if flux_type == 'PDCSAP' else res.SAP_FLUX.data[1:]
            for d in data:
                lc = lc.append(mag(d))

    lc = lc.remove_nans()
    lc = lc.remove_outliers(4)
    mprint(f"Total observation length: {'%.2f' % (lc.time[-1] - lc.time[0])} days.",log)
    return lc