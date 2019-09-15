import numpy as np
from lightkurve import Periodogram as lk_Periodogram,LightCurve
from astropy.stats import LombScargle
from astropy.units import cds
from pandas import DataFrame as df


class Periodogram:
    def __init__(self, frequency: np.ndarray, power: np.ndarray, nyquist: float = None, targetid=None,
                 default_view='frequency', meta={}):
        """
        Custom Periodogramm class. Mirrors the behaviour of lightkurve.periodogramm. See lightkurve docs
        for info
        """
        self.nyquist = nyquist
        self.pdg = lk_Periodogram(frequency,power,nyquist=nyquist,targetid=targetid,default_view=default_view,meta=meta)

    @property
    def max_power(self):
        return self.pdg.max_power

    @property
    def frequency_at_max_power(self):
        return self.pdg.frequency_at_max_power

    @property
    def frequency(self):
        return self.pdg.frequency

    @property
    def power(self):
        return self.pdg.power

    @staticmethod
    def from_lightcurve(lc : LightCurve, f_min=None, f_max=None, remove_ranges = None
                        , samples_per_peak = 10):

        nyquist = 1/(2*np.median(np.diff(lc.time)))

        try:
            time = lc.time.value
        except AttributeError:
            time = lc.time

        try:
            flux = lc.flux.value
        except AttributeError:
            flux = lc.flux


        ls = LombScargle(time,flux,normalization='psd')

        if f_max is not None and f_max > nyquist:
            #todo warning here!
            pass

        if f_max is None:
            f_max = nyquist

        f, p = ls.autopower(minimum_frequency=f_min, maximum_frequency=f_max,
                            samples_per_peak=samples_per_peak, nyquist_factor=1)

        # normalization of psd in order to get good amplitudes
        p = np.sqrt(4 / len(time)) * np.sqrt(p)

        # removing first item
        p = p[1:]
        f = f[1:]

        if remove_ranges is not None:
            mask_list = []
            for r in remove_ranges:
                mask = f < r[0]
                mask = np.logical_or(mask,f > r[1])
                mask_list.append(mask)

            combined_mask = mask_list[0]
            if len(mask_list) > 1:
                for m in mask_list[1:]:
                    combined_mask = np.logical_and(combined_mask,m)

            f = f[combined_mask]
            p = p[combined_mask]

        return Periodogram(f*(1/cds.d),p*cds.ppm,nyquist=nyquist,targetid=lc.targetid)

    def plot(self,scale='linear', ax=None, xlabel=None, ylabel=None, title='', style='lightkurve', view=None,
             unit=None,color='k', **kwargs):

        return self.pdg.plot(scale,ax,xlabel,ylabel,title,style,view,unit,linestyle='-',color=color,**kwargs)

    def to_csv(self,file):
        frame = df.from_dict({'Frequency':self.pdg.frequency,'Power':self.pdg.power})
        frame.to_csv(file)