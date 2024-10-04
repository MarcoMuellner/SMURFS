import lightkurve as lk
import numpy as np
from astropy.time import Time
from scipy.optimize import curve_fit
from uncertainties import ufloat, unumpy as unp
import matplotlib.pyplot as pl
from matplotlib.axes import Axes
from uncertainties.core import AffineScalarFunc
from lmfit import Model
from typing import Union, List, Tuple
from pandas import DataFrame as df
import astropy.units as u
from uncertainties.core import Variable

from smurfs.signal.periodogram import Periodogram
from smurfs.signal.lightcurve import LightCurve
from smurfs.support.mprint import *


def sin(x: np.ndarray, amp: float, f: float, phase: float) -> np.ndarray:
    """
    Sinus function, used for fitting.

    :param x: Time axis, days
    :param amp: amplitude, mag
    :param f: frequency, c/d
    :param phase: phase, normed to 1
    """
    if isinstance(x, Time):
        x = x.jd
    return amp * np.sin(2. * np.pi * (f * x + phase))


def sin_multiple(x: np.ndarray, *params) -> np.ndarray:
    """
    Multiple sinuses summed up

    :param x: Time axis
    :param params: Params, see *sin* for signature
    """
    y = np.zeros(len(x))
    for i in range(0, len(params), 3):
        y += sin(x, params[i], params[i + 1], params[i + 2])

    return y


def m_od_uncertainty(lc: LightCurve, a: float) -> Tuple:
    """
    Computes uncertainty for a given light curve according to Montgomery & O'Donoghue (1999).

    :param lc: :meth:`smurfs.Lightcurve` object
    :param a: amplitude of the frequency
    :return: A tuple of uncertainties in this order: Amplitude, frequency, phase
    """
    # computation of uncertainties with Montgomery & O'Donoghue (1999), used when there are no
    # uncertainties in the flux of the light curve
    N = len(lc.flux)
    sigma_m = np.std(lc.flux)
    sigma_amp = np.sqrt(2 / N) * sigma_m
    sigma_f = np.sqrt(6 / N) * (1 / (np.pi * max(lc.time.jd) - min(lc.time.jd))) * sigma_m / a
    sigma_phi = np.sqrt(2 / N) * sigma_m / (a * (2 * np.pi))
    try:
        return sigma_amp.value, sigma_f.value, sigma_phi.value
    except AttributeError:
        return sigma_amp, sigma_f, sigma_phi


class Frequency:
    """
    The Frequency class represents a single frequency of a given data set. It takes the frequency of maximum
    power as the guess for pre-whitening. It also computes the Signal to noise ratio of that frequency.
    After instantiating this class, you can call *pre-whiten*, which tries to fit the frequency to
    the light curve, and returns the residual between the original light curve and the model of
    the frequency.

    :param time: Time axis
    :param flux: Flux axis
    :param window_size: Window size, used to compute the SNR
    :param snr: Lower end signal to noise ratio, defines if a frequency is marked as significant
    :param flux_err: Error in the flux
    :param f_min: Lower end of the frequency range considered. If None, it uses 0
    :param f_max: Upper end of the frequency range considered. If None, it uses the Nyquist frequency
    :param rm_ranges: Ranges of frequencies, that should be ignored (List of tuples, that contain a f_min -> f_max range. These areas are ignored)
    """

    def __init__(self, time: np.ndarray, flux: np.ndarray, window_size: float, snr: float, flux_err: np.ndarray = None,
                 f_min: float = None, f_max: float = None, rm_ranges: List[Tuple[float]] = None,fit_fun : callable = None):
        if flux_err is None:
            self._lc = LightCurve(lk.LightCurve(time, flux))
        else:
            self._lc = LightCurve(lk.LightCurve(time, flux, flux_err=flux_err))

        self.flux_error = flux_err
        self.pdg: Periodogram = Periodogram.from_lightcurve(self.lc, f_min, f_max, remove_ranges=rm_ranges)

        self.ws = window_size * self.pdg.frequency.unit

        self.find_adjacent_minima()

        self._amp = np.nan
        self._f = np.nan
        self._phase = np.nan
        self._significant = self.snr > snr
        self._label = ""
        self._fit_fun = fit_fun
        self._other_params = None

    @property
    def amp(self) -> Union[float, Variable]:
        """
        Returns the amplitude of the found frequency (in mag)
        """
        return self._amp

    @amp.setter
    def amp(self, value: Union[float, Variable]):
        self._amp = value

    @property
    def f(self) -> Union[float, Variable]:
        """
        Returns the frequency of the found frequency (in c/d)
        """
        return self._f

    @property
    def other_params(self):
        return self._other_params

    @f.setter
    def f(self, value: Union[float, Variable]):
        self._f = value

    @property
    def phase(self) -> Union[float, Variable]:
        """
        Returns the phase of the found frequency (between 0 and 1)
        """
        return self._phase

    @phase.setter
    def phase(self, value: Union[float, Variable]):
        self._phase = value

    @property
    def significant(self) -> bool:
        """
        Returns the significance of the frequency. True --> significant, False --> insignificant
        """
        return self._significant

    @significant.setter
    def significant(self, value: bool):
        self._significant = value

    @property
    def label(self) -> str:
        """
        Returns the label of the found frequency
        """
        return self._label

    @label.setter
    def label(self, value: str):
        self._label = value

    @property
    def lc(self) -> LightCurve:
        """
        Represents the light curve on which the analysis is performed
        """
        return self._lc

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

    def scipy_fit(self) -> Tuple[Variable,Variable,Variable,Tuple[float,float,float]]:
        """
        Performs a scipy fit on the light curve of the object. Limits are 50% up and down from the initial guess.
        Computes uncertainties using the provided covariance matrix from curve_fit.

        :return: values for amplitude,frequency, phase (in this order) including their uncertainties, as well as the param object
        """

        f_guess = self.pdg.frequency_at_max_power.value
        amp_guess = self.pdg.max_power.value

        arr = [amp_guess,  # amplitude
               f_guess,  # frequency
               0  # phase --> set to center
               ]
        limits = [[0.5 * amp_guess, 0.5 * f_guess, 0], [1.5 * amp_guess, 1.5 * f_guess, 1]]
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

    def lmfit_fit(self) -> Tuple[Variable,Variable,Variable,List[float]]:
        """
        Uses lmfit to perform the sin fit on the light curve. We first fit all three free parameters, and then vary
        the phase parameter, to get a more accurate value for it. Uncertainties are computed according to
        Montgomery & O'Donoghue (1999).

        :return: values for amplitude,frequency, phase (in this order) including their uncertainties, as well as the param object
        """

        f_guess = self.pdg.frequency_at_max_power.value
        amp_guess = self.pdg.max_power.value

        model = Model(sin)
        model.set_param_hint('amp', value=amp_guess, min=0.8 * amp_guess, max=1.2 * amp_guess)
        #model.set_param_hint('f', value=f_guess, min=0.5 * f_guess, max=1.5 * f_guess)
        model.set_param_hint('f', value=f_guess,vary=False)
        model.set_param_hint('phase', value=0.5, min=0, max=1)

        result = model.fit(self.lc.flux, x=self.lc.time)

        # after first fit, vary only phase
        ph_list = [0.5,0.3,0.7]
        for i in ph_list:
            model = Model(sin)
            model.set_param_hint('amp', value=result.values['amp'], vary=False)
            model.set_param_hint('f', value=result.values['f'], vary=False)
            model.set_param_hint('phase', value=i, min=0, max=1)
            result = model.fit(self.lc.flux, x=self.lc.time)

            a, f, ph = result.values['amp'], result.values['f'], result.values['phase']
            if np.abs(ph-i) > 10**-2:
                break
            else:
                mprint(f"Initial value {i} --> {ph}. Trying another initial value",log)

        if np.abs(ph-ph_list[-1]) < 10**-3:
            mprint(f"Phase is very close to initial value of fit!",warn)

        if self.flux_error is None or True:
            sigma_amp, sigma_f, sigma_phi = m_od_uncertainty(self.lc, a)
            return ufloat(a, sigma_amp), ufloat(f, sigma_f), ufloat(ph, sigma_phi), [a, f, ph]
        else:
            # todo incorporate flux error into fit
            return ufloat(a, 0), ufloat(f, 0), ufloat(ph, 0), [a, f, ph]

    def pre_whiten(self, mode: str = 'lmfit') -> LightCurve:
        """
        'Pre whitens' a given light curve. As an estimate, the method always uses the frequency with maximum power.
        It then performs the fit according to the mode parameter, and returns a Lightcurve object with the reduced
        light curve

        :param mode:'scipy' or 'lmfit'
        :return: Pre-whitened lightcurve object
        """
        if self._fit_fun is not None:
            kwargs = {
                'lc':self.lc,
                'pdg':self.pdg,
                'f_guess':self.pdg.frequency_at_max_power.value,
                'amp_guess':self.pdg.max_power.value
            }
            ret_dict = self._fit_fun(kwargs)
            if not isinstance(ret_dict,dict) or not all(i in ret_dict.keys() for i in ['Amplitude','Frequency','Phase','LC']):
                raise ValueError("If you are using custom fit functions, you need to return a dictionary containing at least:\n"
                                 "1) Amplitude\n2) Frequency\n3) Phase\n4)Pre-whitened light curve")

            self.amp = ret_dict['Amplitude']
            self.f = ret_dict['Frequency']
            self.phase = ret_dict['Phase']
            self._other_params = {}
            for key,val in ret_dict.items():
                if key in ['Amplitude','Frequency','Phase','LC']:
                    continue
                self._other_params[key] = val
            lc = ret_dict['LC']
            return lc
        if mode == 'scipy':
            self.amp, self.f, self.phase, param = self.scipy_fit()
        elif mode == 'lmfit':
            self.amp, self.f, self.phase, param = self.lmfit_fit()
        else:
            raise ValueError("Unknown fit mode")

        return LightCurve(lk.LightCurve(self.lc.time, self.lc.flux - sin(self.lc.time, *param)))

    def plot(self, ax: Axes = None, show=False, use_guess=False) -> Union[None, Axes]:
        """
        Plots the periodogramm. If a fit was already performed, it uses the fit _result by default. This
        can be overwritten by setting use_guess to True

        :param ax: Axis object
        :param show: Shows the plot
        :param use_guess: Uses the guess
        :return: Axis object if plot was not shown
        """
        ax: Axes = self.pdg.plot(ax=ax, ylabel='Amplitude', color='k')
        pwr = self.pdg.max_power / self.snr

        if isinstance(self._f, AffineScalarFunc) and not use_guess:
            f = self._f.nominal_value
            f_str = f'Fit: {self._f} {self.pdg.frequency_at_max_power.unit}'
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
    """
    The FFinder object computes all frequencies according to the input parameters. After instantiating this object,
    use the *run* method to start the computation of frequencies.

    :param smurfs: *Smurfs* object
    :param f_min: Lower bound frequency that is considered
    :param f_max: Upper bound frequency that is considered
    """

    def __init__(self, smurfs, f_min: float = None, f_max: float = None):
        self.f_min = f_min
        self.f_max = f_max
        self.lc: LightCurve = smurfs.lc
        self.pdg: Periodogram = Periodogram.from_lightcurve(self.lc, f_min=f_min, f_max=f_max)
        self.nyquist = smurfs.nyquist

        self._spectral_window = None
        self.rm_ranges = None

        self.columns = ['f_obj', 'frequency', 'amp', 'phase', 'snr', 'res_noise', 'significant']
        self.result = df([], columns=self.columns)

        mprint(f"Periodogramm from {self.pdg.frequency[0].round(2)} to "
               f"{self.pdg.frequency[-1].round(2)}", log)

    def run(self, snr: float = 4, window_size: float = 2, skip_similar: bool = False, similar_chancel=True,
            extend_frequencies: int = 0, improve_fit=True, mode='lmfit',frequency_detection=None, fit_fun : callable = None) -> df:
        """
        Starts the frequency extraction from a light curve. In general, it always uses the frequency of maximum power
        and removes it from the light curve. In general, this process is repeated until we reach a frequency that
        has a SNR below the lower SNR bound. It is possible to extend this process, by setting the *extend_frequencies*
        parameter. It then stops after *extend_frequencies* insignificant frequencies are found.
        If similar_chancel is set, the process also stops after 10 frequencies with a standard deviation of 0.05
        were found in a row.

        :param snr: Lower bound Signal to noise ratio
        :param window_size: Window size, to compute the SNR
        :param skip_similar: If this is set and 10 frequencies with a standard deviation of 0.05 were found in a row, that region will be ignored for all further analysis.
        :param similar_chancel: If this is set and *skip_similar* is **False**, the run chancels after 10 frequencies with a standard deviation of 0.05 were found in a row.
        :param extend_frequencies: Defines the number of insignificant frequencies, the analysis extends to.
        :param improve_fit: If this is set, the combination of frequencies are fitted to the data set to improve the parameters
        :param mode: Fitting mode. Can be either 'lmfit' or 'scipy'
        :param frequency_detection: If this value is not None and the ratio between the amplitude of the found frequency and the amplitude of the frequency in the original spectrum exceeds this value, this frequency is ignored.
        :return: Pandas dataframe, consisting of the results for the analysis. Consists of a *Frequency* object, frequency, amplitude, phase, snr, residual noise and a significance flag.
        """
        # todo incorporate flux error

        if fit_fun is not None and not (callable(fit_fun) or (isinstance(fit_fun,tuple) and len(fit_fun)==2)):
            raise AttributeError("fit_fun must be either a function, or a tuple of two functions")

        #setup custom fit functions
        if isinstance(fit_fun,tuple):
            single_fit = fit_fun[0]
            multiple_fit = fit_fun[1]
        elif fit_fun is not None:
            single_fit = fit_fun
            multiple_fit = None
            if improve_fit:
                mprint(f"Single function passed as fit function, disabling improve fit",info)
                improve_fit = False
        else:
            single_fit = None
            multiple_fit = None

        mprint("Starting frequency extraction.", info)
        skip_similar_text = ctext('Activated' if skip_similar else 'Deactivated', info if skip_similar else error)
        similar_chancel_text = ctext('Activated' if similar_chancel else 'Deactivated',
                                     info if similar_chancel else error)

        f_u = self.pdg.frequency.unit
        a_u = u.mag

        mprint(f"Skip similar: {skip_similar_text}", log)
        mprint(f"Chancel after 10 similar: {similar_chancel_text}", log)
        mprint(f"Window size: {window_size}", log)
        mprint(f"Number of extended frequencies: {extend_frequencies}", log)
        mprint(f"Nyquist frequency: {(self.nyquist * self.pdg.frequency.unit).round(2)}", info)

        lc: LightCurve = self.lc

        result = []
        noise_list = []

        extensions = 0

        mprint(f"List of frequencies, amplitudes, phases, S/N", state)
        try:
            while True:
                f = Frequency(lc.time, lc.flux, window_size, snr, f_min=self.f_min, f_max=self.f_max,
                              rm_ranges=self.rm_ranges,fit_fun= single_fit)

                # check significance of frequency
                if not f._significant:
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


                if frequency_detection is not None:
                    amp = np.amax(self.pdg.power[f.lower_m:f.upper_m])
                    if f.amp/amp.value <0.3:
                        if self.rm_ranges is None:
                            self.rm_ranges = [(self.pdg.frequency[f.lower_m].value,self.pdg.frequency[f.upper_m].value)]
                        else:
                            self.rm_ranges.append((self.pdg.frequency[f.lower_m].value,self.pdg.frequency[f.upper_m].value))
                        mprint(f"{f.f} {f_u}   {f.amp} {a_u}   {f.phase}  can't be detected in original periodogram. "
                               f"Skipping the range between {'%.3f'%self.pdg.frequency[f.lower_m].value} "
                               f"and {'%.3f'%self.pdg.frequency[f.upper_m].value}",warn)
                        continue

                f._label = f"F{len(result)}"

                mprint(f"F{len(result)}   {f.f} {f_u}   {f.amp} {a_u}   {f.phase}   {f.snr} ", state)

                result.append(f)
                noise_list.append(res_noise)

                if improve_fit and multiple_fit is None:
                    result = self._improve_fit(result, mode=mode,fit_fun=multiple_fit)
                    lc = self._res_lc_from_model(result, True)
                if improve_fit and multiple_fit is not None:
                    result,lc = self._improve_fit(result,fit_fun=multiple_fit)

                # check for similarity of last 10 frequencies
                if len(result) > 10:
                    f_list = unp.nominal_values([i._f for i in result])[-10:]
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
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        finally:
            mprint(f"Total frequencies: {len(result)}", info)
            self.res_lc = lc
            self.res_pdg = Periodogram.from_lightcurve(lc, self.f_min, self.f_max)
            if fit_fun is None:
                self.result = df([[i, i.f, i.amp, i.phase, i.snr, j, i.significant] for i, j in zip(result, noise_list)]
                                 , columns=self.columns)
            else:
                data_list = []
                key_list = []
                for i,j in zip(result,noise_list):
                    data_list.append([i,i.f,i.amp,i.phase,i.snr,j,i.significant] + list(i.other_params.values()))
                    key_list = list(i.other_params.keys())
                self.result = df(data_list
                                 , columns=self.columns + key_list)

        return self.result

    def plot(self, ax: Axes = None, show=False, plot_insignificant=False, **kwargs):
        """
        Plots the periodogram of the data set, including the found frequencies.

        :param ax: Axes object
        :param show: Show flag, if True, pylab.show is called
        :param plot_insignificant: If True, insignificant frequencies are shown
        :param kwargs: kwargs for Periodogram.plot
        """
        if 'color' in kwargs.keys():
            color = kwargs['color']
            del kwargs['color']
        else:
            color = 'grey'

        ax: Axes = self.pdg.plot(ax=ax, color=color, ylabel='Amplitude [mag]', **kwargs)

        if plot_insignificant:
            frame = self.result
        else:
            frame: df = self.result[self.result.significant == True].reset_index(drop=True)

        if len(frame) > 0:
            ax.set_xlim(np.amin(frame.frequency).nominal_value * 0.8, np.amax(frame.frequency).nominal_value * 1.2)

        for i in frame.iterrows():
            f = i[1].f_obj.f.nominal_value
            a = i[1].f_obj.amp.nominal_value

            y_min = np.abs(ax.get_ylim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0])
            y_max = (np.abs(ax.get_ylim()[0]) + a) / (ax.get_ylim()[1] - ax.get_ylim()[0])

            ax.axvline(x=f, ymin=y_min, ymax=y_max, color='k')
            ax.annotate(f'f{i[0] + 1}', (f, a))

        if show:
            pl.show()

    def _scipy_fit(self, result: List[Frequency]) -> List[Frequency]:
        """
        Performs a combination fit for all found frequencies using *scipy.optimize.curve_fit*.

        :param result: List of found frequencies
        :return: List of improved frequencies
        """
        arr = []
        boundaries = [[], []]
        for r in result:
            arr.append(r.amp.nominal_value)
            arr.append(r.f.nominal_value)
            arr.append(r.phase.nominal_value)

            boundaries[0] += [r.amp.nominal_value * 0.5, r.f.nominal_value * 0.5, 0]
            boundaries[1] += [r.amp.nominal_value * 1.5, r.f.nominal_value * 1.5, 1]
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

    def _lmfit_fit(self, result: List[Frequency]) -> List[Frequency]:
        """
        Performs a combination fit for all found frequencies using *lmfit*.

        :param result: List of found frequencies
        :return: List of improved frequencies
        """
        models = []
        for f in result:
            m = Model(sin, prefix=f._label)

            m.set_param_hint(f.label + 'amp', value=f.amp.nominal_value, min=0.8 * f.amp.nominal_value,
                             max=1.2 * f.amp.nominal_value)
            m.set_param_hint(f.label + 'f', value=f.f.nominal_value, min=0.8 * f.f.nominal_value,
                             max=1.2 * f.f.nominal_value)
            m.set_param_hint(f.label + 'phase', value=f.phase.nominal_value, min=0.8 * f.phase.nominal_value,
                             max=1.2 * f.phase.nominal_value)
            models.append(m)

        model: Model = np.sum(models)
        try:
            fit_result = model.fit(self.lc.flux.value, x=self.lc.time)
        except AttributeError:
            fit_result = model.fit(self.lc.flux, x=self.lc.time)

        for f in result:
            sigma_amp, sigma_f, sigma_phi = m_od_uncertainty(self.lc, fit_result.values[f._label + 'amp'])
            f.amp = ufloat(fit_result.values[f.label + 'amp'], sigma_amp)
            f.f = ufloat(fit_result.values[f.label + 'f'], sigma_f)
            f.phase = ufloat(fit_result.values[f.label + 'phase'], sigma_phi)

        return result

    def _improve_fit(self, result: List[Frequency], mode='lmfit', fit_fun :callable = None) -> Union[List[Frequency],Tuple[List[Frequency],LightCurve]]:
        """
        Performs a combination fit for all found frequencies.

        :param result: List of found frequencies
        :param mode: Method used, either 'scipy' or 'lmfit'
        :return:
        """
        if fit_fun is not None:
            ret_val = fit_fun(result,self.lc)
            if not isinstance(ret_val,tuple) or len(ret_val) != 2 or not isinstance(ret_val[0],list) or any(not isinstance(i,Frequency) for i in ret_val[0]):
                raise ValueError("Improve fit must return a list of frequency objects!")

            return ret_val
        if mode == 'scipy':
            return self._scipy_fit(result)
        elif mode == 'lmfit':
            return self._lmfit_fit(result)
        else:
            raise ValueError(f"Fitting mode '{mode}' not available.")

    def _res_lc_from_model(self, result: List[Frequency], use_insignificant=False) -> LightCurve:
        """
        Removes the model from the original light curve, giving the residual
        :param result: List of Frequency objects
        :return: Residual LightCurve
        """
        params = []

        for f in result:
            if not f._significant and not use_insignificant:
                continue

            params.append(f.amp.nominal_value)
            params.append(f.f.nominal_value)
            params.append(f.phase.nominal_value)

        try:
            return LightCurve(lk.LightCurve(self.lc.time, self.lc.flux - sin_multiple(self.lc.time, *params)))
        except u.UnitConversionError:
            return LightCurve(
                lk.LightCurve(self.lc.time, self.lc.flux - sin_multiple(self.lc.time, *params) * self.lc.flux.unit))

    def improve_result(self,mode ='lmfit') -> df:
        """
        Improves the result by fitting the combined result to the original light curve
        """
        if len(self.result) == 0:
            return self.result

        f_list = self.result.f_obj.tolist()
        f_list = self._improve_fit(f_list,mode)
        self.res_lc = self._res_lc_from_model(f_list)
        self.res_pdg = Periodogram.from_lightcurve(self.res_lc, self.f_min, self.f_max)
        self.result = df(
            [[i, i.f, i.amp, i.phase, i.snr, j, i.significant] for i, j in zip(f_list, self.result.res_noise.tolist())]
            , columns=self.columns)
        return self.result
