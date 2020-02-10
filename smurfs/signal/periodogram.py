import numpy as np
from lightkurve import Periodogram as lk_Periodogram,LightCurve
from astropy.stats import LombScargle
from astropy.units import cds
from pandas import DataFrame as df
from typing import List,Tuple


class Periodogram(lk_Periodogram):
    """
    Custom Periodogram class, fit to the needs of smurfs. Mirrors the behaviour of the Lightkurve Periodogram class,
    and is derived from it. See
    https://docs.lightkurve.org/api/lightkurve.periodogram.Periodogram.html#lightkurve.periodogram.Periodogram for
    documentation on the constructor parameters.

    This class differs from the Lightkurve Periodogram class through two aspects:
    1) It adds a different static method, that converts a Lightcurve object into a periodogram.
    2) The plotting and saving of data has been adapted to fit the needs of smurfs
    """
    def __init__(self, frequency: np.ndarray, power: np.ndarray, nyquist: float = None, targetid=None,
                 default_view='frequency', meta={}):
        self.nyquist = nyquist
        super().__init__(frequency,power,nyquist=nyquist,targetid=targetid,default_view=default_view,meta=meta)

    @staticmethod
    def from_lightcurve(lc : LightCurve, f_min=None, f_max=None, remove_ranges : List[Tuple[float]] = None
                        , samples_per_peak = 10):

        """
        Computes a periodogram from a Lightcurve object and normalizes it according to Parcivals theorem. It then
        reflects the physical values in the Light curve and has the same units. It then returns a Periodogram object.

        It also has a possibility to remove certain ranges from the periodogram.
        :param lc: Lightcurve object
        :param f_min: Lower range for the periodogram
        :param f_max: Upper range for the periodogram
        :param remove_ranges: List of tuples, that represent areas in the periodogram that are ignored. These are
        removed from the periodogram
        :param samples_per_peak: number of samples per peak
        :return: Periodogram object
        """

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

        if f_min is None:
            f_min = 0

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
        """
        Plots the periodogram. Same call signature as lightkurve.periodogram.Periodogram.
        """

        if 'linestyle' in kwargs.keys():
            ls = kwargs['linestyle']
            del kwargs['linestyle']
        else:
            ls = '-'

        if ylabel is not None:
            ylabel = ylabel
        elif 'ylabel' in kwargs.keys():
            ylabel = kwargs['ylabel']
            del kwargs['ylabel']
        else:
            ylabel='Amplitude [mag]'


        return super().plot(scale,ax,xlabel,ylabel,title,style,view,unit,linestyle=ls,color=color,**kwargs)

    def to_csv(self,file):
        """
        Stores the periodogram into a file.
        :param file: File object
        """
        frame = df.from_dict({'Frequency':self.frequency,'Power':self.power})
        frame.to_csv(file,index=False)