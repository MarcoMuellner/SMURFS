import numpy as np
import lightkurve as lk
from lightkurve.periodogram import Periodogram as lkPeriodogram
from astropy.timeseries import LombScargle
from astropy.units import cds
from pandas import DataFrame as df


class Periodogram(lkPeriodogram):
    """
    Custom Periodogram class, fit to the needs of smurfs. Mirrors the behaviour of the Lightkurve Periodogram class,
    and is derived from it.

    This class differs from the Lightkurve Periodogram class through two aspects:
    1) It adds a different static method, that converts a Lightcurve object into a periodogram.
    2) The plotting and saving of data has been adapted to fit the needs of smurfs
    """
    def __init__(self, frequency, power, nyquist=None, targetid=None, label=None, meta={}):
        super().__init__(frequency, power, nyquist=nyquist, targetid=targetid, label=label, meta=meta)

    @staticmethod
    def from_lightcurve(lc: lk.LightCurve, f_min=None, f_max=None, remove_ranges: list[tuple[float]] = None,
                        samples_per_peak=10):
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
        nyquist = 1 / (2 * np.median(np.diff(lc.time.value)))

        time = lc.time.value
        flux = lc.flux.value

        ls = LombScargle(time, flux, normalization='psd')

        if f_max is not None and f_max > nyquist:
            # TODO: Add warning here
            pass

        f_min = 0 if f_min is None else f_min
        f_max = nyquist if f_max is None else f_max

        f, p = ls.autopower(minimum_frequency=f_min, maximum_frequency=f_max,
                            samples_per_peak=samples_per_peak, nyquist_factor=1)

        # normalization of psd in order to get good amplitudes
        p = np.sqrt(4 / len(time)) * np.sqrt(p)

        # removing first item
        p = p[1:]
        f = f[1:]

        if remove_ranges is not None:
            mask = np.ones_like(f, dtype=bool)
            for r in remove_ranges:
                mask &= (f < r[0]) | (f > r[1])
            f = f[mask]
            p = p[mask]

        return Periodogram(f * (1 / cds.d), p * cds.ppm, nyquist=nyquist, targetid=lc.meta.get('targetid'))

    def plot(self, scale='linear', ax=None, xlabel=None, ylabel=None, title='', style='lightkurve', view=None,
             unit=None, color='k', **kwargs):
        """
        Plots the periodogram. Same call signature as lightkurve.periodogram.Periodogram.
        """
        ls = kwargs.pop('linestyle', '-')
        ylabel = ylabel or kwargs.pop('ylabel', 'Amplitude [mag]')

        return super().plot(scale=scale, ax=ax, xlabel=xlabel, ylabel=ylabel, title=title, style=style,
                            view=view, unit=unit, color=color, linestyle=ls, **kwargs)

    def to_csv(self, file):
        """
        Stores the periodogram into a file.
        :param file: File object
        """
        frame = df.from_dict({'Frequency': self.frequency.value, 'Power': self.power.value})
        frame.to_csv(file, index=False)