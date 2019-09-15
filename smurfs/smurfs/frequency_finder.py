from lightkurve import LightCurve
import numpy as np
from scipy.optimize import curve_fit
from uncertainties import ufloat, unumpy as unp
import matplotlib.pyplot as pl
from matplotlib.axes import Axes
from uncertainties.core import AffineScalarFunc
from lmfit import Model
from typing import Union, List
from pandas import DataFrame as df
import astropy.units as u

from smurfs.signal.periodogramm import Periodogram
from smurfs.support.mprint import *


def sin(x: np.ndarray, amp: float, f: float, phase: float) -> np.ndarray:
    return amp * np.sin(2. * np.pi * (f * x + phase))


def sin_multiple(x: np.ndarray, *params):  # amp_list: List[float], f_list : List[float], phase_list : List[float]):
    y = np.zeros(len(x))
    for i in range(0, len(params), 3):
        y += sin(x, params[i], params[i + 1], params[i + 2])

    return y


class Frequency:
    def __init__(self, time, flux, window_size, snr, flux_err=None, f_min=None, f_max=None, rm_ranges=None):
        if flux_err is None:
            self.lc = LightCurve(time, flux)
        else:
            self.lc = LightCurve(time, flux, flux_err=flux_err)

        self.flux_error = flux_err
        self.pdg: Periodogram = Periodogram.from_lightcurve(self.lc, f_min, f_max, remove_ranges=rm_ranges)

        self.ws = window_size * self.pdg.frequency.unit

        self.find_adjacent_minima()

        self.amp = np.nan
        self.f = np.nan
        self.phase = np.nan
        self.significant = self.snr > snr

    @property
    def snr(self) -> float:
        """
        Computes the signal to noise ratio of a given frequency. It considers the area from the first minima before
        the peak until window halfed, as well as the area from the first minima after the peak until window halfed.
        :return: Signal to noise ratio of the peak
        """
        self.snr_mask = self.pdg.frequency[self.lower_m] - self.ws / 2 < self.pdg.frequency  # mask lower window
        self.snr_mask = np.logical_and(self.snr_mask, self.pdg.frequency < self.pdg.frequency[
            self.upper_m] + self.ws / 2)  # mask upper window
        outside = np.mean(self.pdg.power[self.snr_mask])
        return (self.pdg.max_power / outside).value  # No quantitiy needed here

    def scipy_fit(self):
        """
        Performs a scipy fit on the light curve of the object. Restricts everything to a sensible range.
        :return: uncertainty objects of amplitude,frequency, phase (in this order) as well as the param object
        """

        f_guess = self.pdg.frequency_at_max_power.value
        amp_guess = self.pdg.max_power.value

        arr = [amp_guess,  # amplitude
               f_guess,  # frequency
               0  # phase --> set to center
               ]
        limits = [[0*5*amp_guess, 0.5*f_guess, 0], [1.5*amp_guess, 1.5*f_guess, 1]]
        try:
            popt, pcov = curve_fit(sin, self.lc.time, self.lc.flux, p0=arr, bounds=limits)
        except RuntimeError:
            try:
                popt, pcov = curve_fit(sin, self.lc.time, self.lc.flux, p0=arr, bounds=limits,
                                       maxfev=400 * (len(self.lc.time) + 1))
            except RuntimeError:
                raise RuntimeError(
                    ctext(f"Failed to find a good fit for frequency {self.pdg.frequency_at_max_power}. Consider"
                          f" using the 'lmfit' fitting method.", error))
        perr = np.sqrt(np.diag(pcov))

        return ufloat(popt[0], perr[0]), ufloat(popt[1], perr[0]), ufloat(popt[2], perr[0]), popt

    def lmfit_fit(self):
        """
        Uses lmfit to perform the sin fit on the light curve.
        :return:
        """

        f_guess = self.pdg.frequency_at_max_power.value
        amp_guess = self.pdg.max_power.value

        model = Model(sin)
        model.set_param_hint('amp', value=self.pdg.max_power.value, min=0.5*amp_guess, max=1.5*amp_guess)
        model.set_param_hint('f', value=self.pdg.frequency_at_max_power.value, min=0.5*f_guess, max=1.5*f_guess)
        model.set_param_hint('phase', value=0, min=0, max=1)

        result = model.fit(self.lc.flux, x=self.lc.time)
        a, f, ph = result.values['amp'], result.values['f'], result.values['phase']

        if self.flux_error is None:
            # computation of uncertainties with Montgomery & O'Donoghue (1999), used when there are no
            # uncertainties in the flux of the light curve
            N = len(self.lc.flux)
            sigma_m = np.std(self.lc.flux)
            sigma_amp = np.sqrt(2 / N) * sigma_m
            sigma_f = np.sqrt(6 / N) * (1 / (np.pi * max(self.lc.time) - min(self.lc.time))) * sigma_m / a
            sigma_phi = np.sqrt(2 / N) * sigma_m / a
            return ufloat(a, sigma_amp), ufloat(f, sigma_f), ufloat(ph, sigma_phi), [a, f, ph]
        else:
            # todo incorporate flux error into fit
            return ufloat(a, 0), ufloat(f, 0), ufloat(ph, 0), [a, f, ph]

    def pre_whiten(self, mode: str = 'scipy') -> LightCurve:
        """
        'Pre whitens' a given light curve. As an estimate, the method always uses the frequency with maximum power.
        It then performs the fit according to the mode parameter, and returns a Lightcurve object with the reduced
        light curve
        :param mode:'scipy' or 'lmfit'
        :return: Pre-whitened lightcurve object
        """
        if mode == 'scipy':
            self.amp, self.f, self.phase, param = self.scipy_fit()
        elif mode == 'lmfit':
            self.amp, self.f, self.phase, param = self.lmfit_fit()
        else:
            raise ValueError("Unknown fit mode")

        return LightCurve(self.lc.time, self.lc.flux - sin(self.lc.time, *param))

    def plot(self, ax: Axes = None, show=False, use_guess=False) -> Union[None, Axes]:
        """
        Plots the periodogramm. If a fit was already performed, it uses the fit result by default. This
        can be overwritten by setting use_guess to True
        :param ax: Axis object
        :param show: Shows the plot
        :param use_guess: Uses the guess
        :return: Axis object if plot was not shown
        """
        ax: Axes = self.pdg.plot(ax=ax, ylabel='Amplitude', color='k')
        pwr = self.pdg.max_power / self.snr

        if isinstance(self.f, AffineScalarFunc) and not use_guess:
            f = self.f.nominal_value
            f_str = f'Fit: {self.f} {self.pdg.frequency_at_max_power.unit}'
            color = 'red'
        else:
            f = self.pdg.frequency_at_max_power.value
            f_str = f"Guess: {'%.2f' % f} {self.pdg.frequency_at_max_power.unit}"
            color = 'k'

        ax.set_xlim(self.pdg.frequency[self.snr_mask][0].value * 0.2, self.pdg.frequency[self.snr_mask][-1].value * 2)
        ax.fill_between(self.pdg.frequency[self.snr_mask].value, 0, pwr, facecolor='grey', alpha=0.5, label='Window')
        ax.axvline(x=f, color=color, linestyle='dashed', label=f_str)
        pl.legend()
        if show:
            pl.show()
        else:
            return ax

    def find_adjacent_minima(self):
        """
        Finds the adjacent minima to the guessed frequency, and sets them within the class.
        """

        def checkMinima(yData: np.ndarray, counter: int) -> bool:
            return yData[counter] < yData[counter + 1] and yData[counter] < yData[counter - 1]

        max_indx = int(np.argmin(np.abs(self.pdg.frequency - self.pdg.frequency_at_max_power)))

        counter = 1
        lowerMinima = -1
        upperMinima = -1

        while lowerMinima == -1 or upperMinima == -1:
            negCounter = max_indx - counter
            posCounter = max_indx + counter

            if negCounter - 1 < 0:
                lowerMinima = 0
            elif checkMinima(self.pdg.power, negCounter):
                lowerMinima = negCounter

            if posCounter + 1 >= len(self.pdg.frequency):
                upperMinima = len(self.pdg.frequency) - 1
            elif checkMinima(self.pdg.power, posCounter):
                upperMinima = posCounter

            counter += 1

        self.lower_m, self.upper_m = lowerMinima, upperMinima


class FFinder:
    def __init__(self, smurfs, f_min: float = None, f_max: float = None):
        self.f_min = f_min
        self.f_max = f_max
        self.lc: LightCurve = smurfs.lc
        self.lc.time -= self.lc.time[0]
        self.periodogramm: Periodogram = Periodogram.from_lightcurve(self.lc, f_min=f_min, f_max=f_max)
        self.nyquist = smurfs.nyquist

        self._spectral_window = None
        self.rm_ranges = None

        self.columns = ['f_obj', 'frequency', 'amp', 'phase', 'snr', 'res_noise', 'significant']
        self.result = df([], columns=self.columns)

        mprint(f"Periodogramm from {self.periodogramm.frequency[0].round(2)} to "
               f"{self.periodogramm.frequency[-1].round(2)}", log)

    def run(self, snr: float = 4, window_size: float = 2, skip_similar: bool = False, similar_chancel=True,
            extend_frequencies: int = 0, improve_fit=True, mode='scipy'):

        # todo refit all signals
        # todo return fitted light curve
        # todo incorporate error

        mprint("Starting frequency extraction.", info)
        skip_similar_text = ctext('Activated' if skip_similar else 'Deactivated', info if skip_similar else error)
        similar_chancel_text = ctext('Activated' if similar_chancel else 'Deactivated',
                                     info if similar_chancel else error)

        f_u = self.periodogramm.frequency.unit
        a_u = u.mag

        mprint(f"Skip similar: {skip_similar_text}", log)
        mprint(f"Chancel after 10 similar: {similar_chancel_text}", log)
        mprint(f"Window size: {window_size}", log)
        mprint(f"Number of extended frequencies: {extend_frequencies}", log)
        mprint(f"Nyquist frequency: {(self.nyquist * self.periodogramm.frequency.unit).round(2)}", info)

        lc: LightCurve = self.lc

        result = []
        noise_list = []

        extensions = 0

        mprint(f"List of frequencies, amplitudes, phases, S/N", state)
        while True:
            f = Frequency(lc.time, lc.flux, window_size, snr, f_min=self.f_min, f_max=self.f_max,
                          rm_ranges=self.rm_ranges)

            # check significance of frequency
            if not f.significant:
                if extensions >= extend_frequencies:
                    mprint(f"Stopping extraction after {len(result)} frequencies.", warn)
                    break
                else:
                    mprint(f"Found insignificant frequency, extending extraction ... ", warn)
                    extensions += 1  # extend frequencies after last snr cutoff
            else:
                extensions = 0

            lc = f.pre_whiten(mode)
            res_noise = np.mean(lc.flux)

            mprint(f"F{len(result)}   {f.f} {f_u}   {f.amp} {a_u}   {f.phase}   {f.snr} ", state)

            result.append(f)
            noise_list.append(res_noise)

            if improve_fit:
                self._improve_fit(result)

            # check for similarity of last 10 frequencies
            if len(result) > 10:
                f_list = unp.nominal_values([i.f for i in result])[-10:]
                stdDev = f_list.std()
                if stdDev < 0.05 and skip_similar:
                    mprint(f"Last 10 frequencies where too similar. Skipping region between "
                           f"{'%.2f' % (f_list.mean() - 10 * stdDev)} {f_u} and "
                           f"{'%.2f' % (f_list.mean() + 10 * stdDev)} {f_u}.", warn)
                    if self.rm_ranges is None:
                        self.rm_ranges = [(f_list.mean() - 10 * stdDev, f_list.mean() + 10 * stdDev)]
                    else:
                        self.rm_ranges.append((f_list.mean() - 10 * stdDev, f_list.mean() + 10 * stdDev))
                elif stdDev < 0.05 and similar_chancel:
                    mprint(f"Last 10 frequencies had a std dev of {'%.2f' % stdDev}. Stopping run.", warn)
                    break

        mprint(f"Total frequencies: {len(result)}", info)
        self.res_lc = lc
        self.res_pdg = Periodogram.from_lightcurve(lc, self.f_min, self.f_max)
        self.result = df([[i, i.f, i.amp, i.phase, i.snr, j, i.significant] for i, j in zip(result, noise_list)]
                         , columns=self.columns)
        return self.result

    def plot(self, ax: Axes = None, show=False, plot_insignificant=False, **kwargs):
        ax: Axes = self.periodogramm.plot(ax=ax, color='grey', **kwargs)

        if plot_insignificant:
            frame = self.result
        else:
            frame: df = self.result[self.result.significant == True].reset_index(drop=True)

        for i in frame.iterrows():
            f = i[1].f_obj.f.nominal_value
            a = i[1].f_obj.amp.nominal_value

            y_min = np.abs(ax.get_ylim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0])
            y_max = (np.abs(ax.get_ylim()[0]) + a) / (ax.get_ylim()[1] - ax.get_ylim()[0])

            ax.axvline(x=f, ymin=y_min, ymax=y_max, color='k')
            ax.annotate(f'f{i[0]}', (f, a))

        if show:
            pl.show()

    def _scipy_fit(self, result: List[Frequency]) -> List[Frequency]:
        arr = []
        boundaries = [[],[]]
        for r in result:
            arr.append(r.amp.nominal_value)
            arr.append(r.f.nominal_value)
            arr.append(r.phase.nominal_value)

            boundaries[0] += [r.amp.nominal_value*0.5, r.f.nominal_value*0.5, 0]
            boundaries[1] += [r.amp.nominal_value*1.5, r.f.nominal_value*1.5, 1]
        try:
            popt, pcov = curve_fit(sin_multiple, self.lc.time, self.lc.flux, p0=arr)
        except RuntimeError:
            mprint(f"Failed to improve first {len(result)} frequencies. Skipping fit improvement.", warn)
            return result
        perr = np.sqrt(np.diag(pcov))
        for r, vals in zip(result,
                           [[ufloat(popt[i + j], perr[i + j]) for j in range(0, 3)] for i in range(0, len(popt), 3)]):
            r.amp = vals[0]
            r.f = vals[1]
            r.phase = vals[2]
        return result

    def _lmfit_fit(self, result: List[Frequency]):
        pass

    def _improve_fit(self, result: List[Frequency], mode='scipy') -> List[Frequency]:
        if mode == 'scipy':
            return self._scipy_fit(result)
        elif mode == 'lmfit':
            return self._lmfit_fit(result)
        else:
            raise ValueError(f"Fitting mode '{mode}' not available.")
