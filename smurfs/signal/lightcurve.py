import lightkurve as lk
import astropy.units as u
from typing import Union
from matplotlib.axes import Axes

class LightCurve (lk.TessLightCurve):
    """
    Custom LightCurve object. Reimplements the plot routine, as we only use mag within SMURFS

    :param lc: Lightcurve object
    """
    def __init__(self, lc : Union[lk.TessLightCurve,lk.LightCurve]):
        if isinstance(lc,lk.TessLightCurve):
            super().__init__(time=lc.time,flux=lc.flux,flux_err=lc.flux_err,flux_unit=lc.flux_unit,time_format=lc.time_format,
                             centroid_col=lc.centroid_col,centroid_row=lc.centroid_row,quality=lc.quality,
                             quality_bitmask=lc.quality_bitmask,cadenceno=lc.cadenceno,sector=lc.sector,
                             camera=lc.camera, ccd=lc.ccd,targetid=lc.targetid,ra=lc.ra,dec=lc.dec,label=lc.label,
                             meta=lc.label)
        else:
            super().__init__(time=lc.time,flux=lc.flux,flux_err=lc.flux_err,time_format=lc.time_format,
                             time_scale=lc.time_scale,targetid=lc.targetid,label=lc.label,meta=lc.meta)

    def plot(self,**kwargs):
        ax: Axes = super().plot(color='k', ylabel="Flux [mag]", normalize=False, **kwargs)
        ax.set_ylim(ax.get_ylim()[::-1])

        return ax

    def scatter(self,**kwargs):
        ax: Axes = super().scatter(color='k', ylabel="Flux [mag]", normalize=False, **kwargs)
        ax.set_ylim(ax.get_ylim()[::-1])

        return ax