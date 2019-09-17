import sys

if not sys.warnoptions:
    import warnings

    warnings.simplefilter("ignore")

from lightkurve import LightCurve, TessLightCurve
import matplotlib.pyplot as pl
import numpy as np
from pandas import DataFrame as df
import os
import pickle
from numba import jit
from pyfcomb import get_combinations
from uncertainties import unumpy as unp
from matplotlib.axes import Axes

from smurfs.preprocess.tess import download_lc
from smurfs.preprocess.file import load_file
from smurfs._smurfs.frequency_finder import FFinder, sin_multiple
from smurfs.signal.periodogram import Periodogram
from smurfs.support.support import cd
import smurfs.support.mprint as mpr
from smurfs.support.mprint import *


@jit(nopython=True, parallel=True)
def _jit_spectral_window(f, t):
    W = []
    w = np.exp(2 * np.pi * 1j * t)

    for i in f:
        W.append(np.sum(np.power(w, i)))

    p = np.abs((1 / len(t)) * np.array(W))

    return f, p


class Smurfs:
    """
    The *Smurfs* class is the main way to start your frequency analysis. The workflow for a generic problem is the
    following:

    1) Instantiate the *Smurfs* class, by providing the light curve through one of different methods.
    2) Call 'run', by providing at least the signal to noise ratio and window size of the analysis.
    3) Either save the analysis using 'save' or get the result from the class and continue your analysis.

    After 'run' has finished, you can access the results through various channels:

    - Use the 'ff' property (returns the 'FFinder' instance, where the analysis happens)
    - Use the 'result' property

    The class also has other interesting properties like 'combinations' (calculates all possible combinations
    for the frequencies from the results, uses [pyfcomb](https://github.com/MarcoMuellner/pyfcomb) ), 'nyquist' (
    the nyquist frequency of the provided data) and more.

    You can also plot the results using the 'plot_lc' or 'plot_pdg' methods.

    You can provide a light curve through three different methods:

    1) Set *target_name*: Can be any star that has been observed by the TESS or Kepler mission. You can provide any TIC or KIC ID (including KIC/TIC) or any name resolvable by Simbad.
    2) Set *time* and *flux*
    3) Set *file*: Needs to be an ASCII file containing time and flux

    Either can be used. 1) and 2) will be automatically sigma clipped and converted to magnitude.
    :param file: ASCII file containing time and flux
    :param time: time column of the light curve
    :param flux: flux column of the light curve
    :param target_name: Name of the target, resolvable by Simbad or either KIC/TIC ID
    :param flux_type: If you supply a target name that has been observed by TESS SC mode, you can choose either 'PCDSAP' or 'SAP' flux for that target.
    :param label: Optional label for the star. Results will be saved under this name
    :param quiet_flag: Quiets Smurfs (no more print message will be piped to stdout)
    """
    def __init__(self, file=None, time=None, flux=None, target_name=None, flux_type='PDCSAP', label=None, quiet_flag=False):
        mpr.quiet = quiet_flag
        if target_name is not None:
            self.lc: TessLightCurve = download_lc(target_name, flux_type)
            if label is None:
                self.label = target_name
            else:
                self.label = label
        elif time is None and flux is None and file is None:
            raise AttributeError(ctext("You need to either pass a target path or time and flux of the lightcurve object",error))
        elif time is not None and flux is not None:
            mprint("Creating light curve object from time and flux input.",log)
            self.lc: LightCurve = LightCurve(time=time, flux=flux)
            if label is None:
                self.label = 'LC'
            else:
                self.label = label
        elif file is not None:
            self.lc: LightCurve = load_file(file)
            if label is None:
                self.label = os.path.basename(file).split(".")[0]
            else:
                self.label = label

        else:
            raise AttributeError(ctext("You need to either pass a target path or time and flux of the lightcurve object",error))

        self.pdg: Periodogram = Periodogram.from_lightcurve(self.lc)
        self._result = df([], columns=['f_obj', 'frequency', 'amp', 'phase', 'snr', 'res_noise', 'significant'])
        self._combinations = df([],
                                columns=["Name", "ID", "Frequency", "Amplitude", "Solution", "Residual", "Independent",
                                        "Other_Solutions"])
        self._ff: FFinder = None
        self._spectral_window = None

        #Original light curve to perform some processsing on that
        self.original_lc = self.lc.copy()

        #Target settings
        self.target_name = target_name
        self.flux_type = flux_type

        #Frequency settings
        self.snr = np.nan
        self.window_size = np.nan
        self.f_min = np.nan
        self.f_max = np.nan
        self.skip_similar = None
        self.similar_chanel = None
        self.extend_frequencies = np.nan

        mprint(f"Duty cycle for {self.label}: {'%.2f' % (self.duty_cycle*100)}%",info)

    @property
    def combinations(self):
        """
        Gives a pandas dataframe of all possible combinations for the frequencies from *result*. It consists
        of the following columns in this order:

        - Name: Name of the frequency
        - ID: Frequency ID (order in which it was removed from the light curve)
        - Frequency: The frequency for which combinations where searched.
        - Amplitude: Amplitude of the frequency
        - Solution: Best solution for this frequency
        - Residual: Residual for the best solution
        - Independent: Flag if the frequency is independent according to the solver
        - Other_solutions: All other possible solutions for this frequency

        Will be populated after *run* was called.
        """
        return self._combinations

    @property
    def result(self):
        """
        Gives a pandas dataframe of the result from smurfs. It consists of the following columns in this order:

        - f_obj: *Frequency* object, that represents a given frequency
        - frequency
        - amp
        - phase
        - snr
        - res_noise: Residual noise
        - significant: Flag that shows if a frequency is significant or not
        """
        return self._result

    @property
    def ff(self):
        """
        Returns the *FrequencyFinder* object.
        """
        return self._ff

    @property
    def settings(self):
        """
        Returns a dataframe consising of the settings used in the analysis.
        """
        columns = ['Signal to Noise Ratio',
                   'Window size',
                   'Lower frequency bound',
                   'Upper frequency bound',
                   'Skip similar frequency regions',
                   'Chancel run after 10 similar frequencies',
                   'Ignore unsignificant frequencies number',
                   ]
        return df([[self.snr, self.window_size, self.f_min, self.f_max, self.skip_similar, self.similar_chanel
                       , self.extend_frequencies]], columns=columns)

    @property
    def statistics(self):
        """
        Returns a dataframe consisting of various statistics of the run.
        """
        columns = ['Duty cycle',
                   'Nyquist frequency',
                   'Total number of found frequencies']
        return df([[self.duty_cycle, self.nyquist, len(self._result)]], columns=columns)

    @property
    def obs_length(self):
        """
        Returns the length of the data set.
        """
        return self.lc.time[-1] - self.lc.time[0]

    @property
    def nyquist(self):
        """
        Returns the nyquist frequency
        """
        return 1 / (2 * np.median(np.diff(self.lc.time)))

    @property
    def duty_cycle(self):
        """
        Shows the duty cycle of the light curve
        """
        diff = np.diff(self.lc.time)
        t = np.median(diff)
        std = np.std(diff)
        mask = diff > (t + 3 * std)
        return (1 - np.sum(diff[mask]) / np.sum(diff))

    @property
    def periodogramm(self):
        """
        Returns a *Periodogram* object of the light curve.
        """
        return self.pdg

    @property
    def spectral_window(self):
        """
        Computes the spectral window of a given dataset by transforming the light curve with constant flux.
        """
        if self._spectral_window is None:
            spec_lc = self.lc.copy()
            spec_lc.flux = np.zeros(len(self.lc.flux)) + 1
            self._spectral_window = Periodogram.from_lightcurve(spec_lc)
        return self._spectral_window

    def fold(self, period, t0=None, transit_midpoint=None):
        """
        Returns a folded light curve. Signature equivalent to *lightkurve.LightCurve.fold*.
        """
        return self.lc.fold(period, t0, transit_midpoint)

    def flatten(self, window_length=101, polyorder=2, return_trend=False, break_tolerance=5, niters=3, sigma=3,
                mask=None, **kwargs):
        """
        Flattens the light curve by applying a Savitzky Golay filter. Signature equivalent to
        *lightkurve.LightCurve.flatten*.
        """
        if return_trend:
            self.lc, self.trend = self.original_lc.flatten(window_length, polyorder, return_trend, break_tolerance, niters,
                                                  sigma, mask, **kwargs)
        else:
            self.lc = self.original_lc.flatten(window_length, polyorder, return_trend, break_tolerance, niters, sigma, mask,
                                      **kwargs)

        self.lc = self.lc.remove_outliers(4)
        self.lc = self.lc.remove_nans()
        self.pdg: Periodogram = Periodogram.from_lightcurve(self.lc)

    def run(self, snr: float = 4, window_size: float = 2, f_min: float = None, f_max: float = None,
            skip_similar: bool = False, similar_chancel=True, extend_frequencies: int = 0,improve_fit = True,
            mode='lmfit'):
        """
        Starts the frequency analysis by instantiating a *FrequencyFinder* object and running it. After finishing the
        run, combinations are computed. See *FrequencyFinder.run* for an explanation of the algorithm.

        :param snr: Signal to noise ratio, that provides a lower end of the analysis.
        :param window_size: Window size, with which the SNR is computed.
        :param f_min: Minimum frequency that is considered in the analysis.
        :param f_max: Maximum frequency that is considered in the analysis.
        :param skip_similar: Flag that skips a certain range if too many similar frequencies in this range are found in a row.
        :param similar_chancel: Flat that chancels the run after 10 frequencies found that are too similar.
        :param extend_frequencies: Extends the analysis by this number of insignificant frequencies.
        :param improve_fit: If this flag is set, all combined frequencies are re-fitted after every new frequency was found
        :param mode: Fitting mode. You can choose between 'scipy' and 'lmfit'
        """

        self.snr = snr
        self.window_size = window_size
        self.f_min = f_min
        self.f_max = f_max
        self.skip_similar = skip_similar
        self.similar_chanel = similar_chancel
        self.extend_frequencies = 0

        self._ff = FFinder(self, f_min, f_max)
        self._result = self._ff.run(snr=snr, window_size=window_size, skip_similar=skip_similar,
                                    similar_chancel=similar_chancel
                                    , extend_frequencies=extend_frequencies, improve_fit=improve_fit, mode=mode)
        self._combinations = get_combinations(self._result.index.tolist(),
                                              unp.nominal_values(self._result.frequency.tolist())
                                              , unp.nominal_values(self._result.amp.tolist()))

        print(f'\x1b[7;32;40m {self.label} Analysis done! \x1b[0m')

    def plot_lc(self, show=False, **kwargs):
        """
        Plots the light curve. If a result is already computed, it also plots the resulting model

        :param show: if this is set, pyplot.show() is called
        :param kwargs: kwargs for *lightkurve.LightCurve.scatter*
        """
        for i in ['color','ylabel','normalize']:
            try:
                del kwargs[i]
            except KeyError:
                pass

        ax : Axes = self.lc.scatter(color='k', ylabel="Flux [mag]",normalize=False, **kwargs)
        if len(self._result) > 0:
            params = []

            for i,j,k in zip(self._result.amp, self._result.frequency, self._result.phase):
                params.append(i.nominal_value)
                params.append(j.nominal_value)
                params.append(k.nominal_value)

            y = sin_multiple(self.lc.time,*params)
            ax.plot(self.lc.time,y,color='red',linewidth=1)
        if show:
            pl.show()

    def plot_pdg(self, show=False, plot_insignificant=False, **kwargs):
        """
        Plots the periodogram. If the result is already computed, it will mark the found frequencies in the
        periodogram.

        :param show: if this is set, pyplot.show() is called
        :param plot_insignificant: Flag, if set, insignififcant frequencies are marked in the perioodogram
        :param kwargs: kwargs for *lightkurve.Periodogram.plot*
        :return:
        """
        if self._ff is None:
            self.pdg.plot(color='k', **kwargs)
        else:
            self._ff.plot(show=show, plot_insignificant=plot_insignificant, **kwargs)

    def save(self, path: str, store_obj=False):
        """
        Saves the result of the analysis to a given folder.

        :param path: Path where the result is stored
        :param store_obj: If this is set, the Smurfs object is stored, and can be later reloaded.
        """
        if not os.path.exists(path):
            raise IOError(ctext(f"'{path}' does not exist!",error))

        mprint("Saving results, this may take a bit ...",warn)

        proj_path = os.path.join(path, self.label)
        index = 1
        while True:
            if not os.path.exists(proj_path):
                break

            proj_path = os.path.join(path, self.label + f"_{index}")
            index += 1

        os.makedirs(proj_path)
        with cd(proj_path):
            os.makedirs("data")
            os.makedirs("plots")

            with cd("data"):
                if self._result is not None:
                    frame: df = self._result.drop(columns=['f_obj'])
                    frame.index.name = 'f_nr'
                    df_list = [(self.settings, '#Settings'),
                               (self.statistics, '#Statistics'),
                               (frame, '#Result')]

                    with open('_result.csv', 'w') as f:
                        for fr, comment in df_list:
                            f.write(f"{comment}\n")
                            fr.to_csv(f)
                            f.write("\n\n")

                    self._combinations.to_csv('_combinations.csv')

                self.lc.to_csv("LC.txt")
                self.pdg.to_csv("PS.txt")
                if self._ff is not None:
                    self._ff.res_lc.to_csv("LC_residual.txt")
                    self._ff.res_pdg.to_csv("PS_residual.txt")

                if store_obj:
                    pickle.dump(self, open("obj.smurfs", "wb"))

            with cd("plots"):
                images = [(self.lc, "LC.pdf"),
                          (self.pdg, "PS.pdf"),
                          ]

                if self._ff is not None:
                    images += [(self._ff.res_lc, "LC_residual.pdf"),
                               (self._ff.res_pdg, "PS_residual.pdf"),
                               (self._ff, "PS_result.pdf")
                               ]

                for obj, name in images:
                    fig, ax = pl.subplots(figsize=(16, 10))
                    if isinstance(obj, LightCurve):
                        obj.scatter(ax=ax, color='k', normalize=False)
                    else:
                        obj.plot(ax=ax, markersize=2)
                    pl.tight_layout()
                    fig.savefig(name)
                    pl.close()
        print(f'\x1b[7;32;40m {self.label} Data saved! \x1b[0m')

    @staticmethod
    def from_path(path : str):
        """
        Loads a smurfs object from path. You need to have set the *store_obj* flag in *save*, for this object to be
        saved.
        """
        if not os.path.exists(path):
            raise IOError(ctext(f"'{path}' does not exist!", error))

        load_file = None

        for r,d,f, in os.walk(path):
            for file in f:
                if '.smurfs' in file:
                    load_file = os.path.join(r,file)

        if load_file is None:
            raise IOError(ctext(f"Can't find any .smurfs file in {path}!"),error)

        return pickle.load(open(load_file,'rb'))



