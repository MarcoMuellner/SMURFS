import os
import pickle
from enum import Enum
from pathlib import Path
from typing import Union, Tuple, Callable

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pandas import DataFrame as df

from smurfs.preprocessing.dataloader import load_data, FluxType, Mission
from smurfs.signal.frequency_finder import FFinder
from smurfs.signal.lightcurve import LightCurve
from smurfs.signal.periodogram import Periodogram
from smurfs.support.mprint import mprint, info, ctext, error, log
from smurfs.support.settings import Settings

on_rtd = os.environ.get('READTHEDOCS') == 'True'
if not on_rtd:
    from pyfcomb import get_combinations
from uncertainties import unumpy as unp


class ImproveFitMode(str, Enum):
    ALL = "all"
    END = "end"
    NONE = "none"


class FitMethod(str, Enum):
    SCIPY = "scipy"
    LMFIT = "lmfit"


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

    :param target: Name of the target, can be either resolvable by Simbad or either KIC/TIC ID, or filename
    :param flux_type: If you supply a target name that has been observed by TESS SC mode, you can choose either 'PCDSAP' or 'SAP' flux for that target.
    :param label: Optional label for the star. Results will be saved under this name
    :param quiet_flag: Quiets Smurfs (no more print message will be piped to stdout)
    """

    def __init__(self, target: str, flux_type: FluxType = FluxType.PDCSAP, label: str = None,
                 quiet_flag: bool = False, mission: Mission = Mission.TESS, sigma_clip: float = 4, iters: int = 1,
                 do_pca: bool = False, do_psf: bool = False, apply_file_correction: bool = False):

        Settings.quiet = quiet_flag

        self.lc = load_data(target, flux_type,sigma_clip, iters, mission)

        if label is None:
            self.label = 'LC'
        else:
            self.label = label

        self.pdg: Periodogram = Periodogram.from_lightcurve(self.lc)
        self._result = df([], columns=['f_obj', 'frequency', 'amp', 'phase', 'snr', 'res_noise', 'significant'])
        self._combinations = df([],
                                columns=["Name", "ID", "Frequency", "Amplitude", "Solution", "Residual", "Independent",
                                         "Other_Solutions"])
        self._ff: FFinder | None = None
        self._spectral_window = None

        # Original light curve to perform some processsing on that
        self.original_lc = self.lc.copy()

        # Target settings
        self.target_name = target
        self.flux_type = flux_type

        # Frequency settings
        self.snr = np.nan
        self.window_size = np.nan
        self.f_min = np.nan
        self.f_max = np.nan
        self.skip_similar = None
        self.similar_chanel = None
        self.extend_frequencies = np.nan
        self._notes = None
        self.validation_page = None

        mprint(f"Duty cycle for {self.label}: {'%.2f' % (self.duty_cycle * 100)}%", info)

    @property
    def combinations(self) -> df:
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
    def result(self) -> df:
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
        raise NotImplementedError("FrequencyFinder is not implemented yet")
        # return self._ff

    @property
    def settings(self) -> df:
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
    def obs_length(self) -> float:
        """
        Returns the length of the data set.
        """
        return (self.lc.time[-1] - self.lc.time[0]).value

    @property
    def nyquist(self) -> float:
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
        diff_array = np.array([d.to('day').value for d in diff])
        t = np.median(diff_array)
        std = np.std(diff_array)
        mask = diff_array > (t + 3 * std)
        return (1 - np.sum(diff_array[mask]) / np.sum(diff_array))

    @property
    def periodogram(self):
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

    @property
    def notes(self):
        return self._notes

    @notes.setter
    def notes(self, value):
        self._notes = value

    def run(self, snr: float = 4, window_size: float = 2, f_min: float = None, f_max: float = None,
            skip_similar: bool = False, similar_chancel: bool = True, extend_frequencies: int = 0,
            improve_fit: bool = True,
            mode: FitMethod = FitMethod.LMFIT, frequency_detection: float | None = None,
            fit_fun: Union[Tuple[Callable, Callable], Callable, None] = None):
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
        :param frequency_detection: If this value is not None and the ratio between the amplitude of the found frequency and the amplitude of the frequency in the original spectrum exceeds this value, this frequency is ignored.
        :param fit_fun: You can pass a function to smurfs to replace its default fit function. SMURFS will pass this function a kwargs object.
        """

        if fit_fun is not None and not (callable(fit_fun) or (isinstance(fit_fun, tuple) and len(fit_fun) == 2)):
            raise AttributeError("fit_fun must be either a function, or a tuple of two functions")

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
                                    , extend_frequencies=extend_frequencies, improve_fit=improve_fit, mode=mode
                                    , frequency_detection=frequency_detection, fit_fun=fit_fun)
        self._combinations = get_combinations((self._result[self._result.significant == True].index + 1).tolist(),
                                              unp.nominal_values(
                                                  self._result[self._result.significant == True].frequency.tolist())
                                              , unp.nominal_values(
                self._result[self._result.significant == True].amp.tolist()))

        self.res_lc = self._ff.res_lc

        mprint(f"{self.label} Analysis done!", info)

    def improve_result(self, mode: FitMethod = FitMethod.LMFIT):
        """
        Fits the combined found frequencies to the original light curve, hence improving the fit of the total model.
        """
        if self._ff is None:
            raise AttributeError("You need to run the analysis before you can improve the fit.")

        self._result = self._ff.improve_result(mode)
        self._combinations = get_combinations((self._result[self._result.significant == True].index + 1).tolist(),
                                              unp.nominal_values(
                                                  self._result[self._result.significant == True].frequency.tolist())
                                              , unp.nominal_values(
                self._result[self._result.significant == True].amp.tolist()))
        self.res_lc = self._ff.res_lc

    def save(self, path: Path, store_obj=False):
        """
        Saves the result of the analysis to a given folder.

        :param path: Path where the result is stored
        :param store_obj: If this is set, the Smurfs object is stored, and can be later reloaded.
        """
        if not path.exists():
            raise IOError(ctext(f"'{path}' does not exist!", error))

        mprint("Saving results, this may take a bit ...", log)
        proj_path = path / self.label.replace(" ", "_")
        index = 1
        while proj_path.exists():
            proj_path = path / f"{self.label.replace(' ', '_')}_{index}"
            index += 1

        proj_path.mkdir(parents=True, exist_ok=True)
        data_path = proj_path / "data"
        plots_path = proj_path / "plots"
        data_path.mkdir()
        plots_path.mkdir()

        # Save data
        if self._result is not None:
            frame: pd.DataFrame = self._result.drop(columns=['f_obj'])
            frame.index.name = 'f_nr'
            df_list = [(self.settings, '#Settings'),
                       (self.statistics, '#Statistics'),
                       (frame, '#Result')]

            with (data_path / 'result.csv').open('w') as f:
                for fr, comment in df_list:
                    f.write(f"{comment}\n")
                    fr.to_csv(f)
                    f.write("\n\n")

            self._combinations.to_csv(data_path / 'combinations.csv')

        # Save light curve data
        lc_data = pd.DataFrame(
            {'time': self.lc.time.value, 'flux': self.lc.flux.value, 'flux_err': self.lc.flux_err.value})
        lc_data.to_csv(data_path / "LC.txt", index=False)

        self.pdg.to_csv(data_path / "PS.txt")

        if self._ff is not None:
            res_lc_data = pd.DataFrame({'time': self._ff.res_lc.time.value, 'flux': self._ff.res_lc.flux.value,
                                        'flux_err': self._ff.res_lc.flux_err.value})
            res_lc_data.to_csv(data_path / "LC_residual.txt", index=False)
            self._ff.res_pdg.to_csv(data_path / "PS_residual.txt")

        if self._notes is not None:
            (data_path / "notes.txt").write_text(self._notes)

        if store_obj:
            with (data_path / "obj.smurfs").open("wb") as f:
                pickle.dump(self, f)

        # Save plots
        images = [(self.lc, "LC.pdf"),
                  (self.pdg, "PS.pdf")]

        if self._ff is not None:
            images += [(self._ff.res_lc, "LC_residual.pdf"),
                       (self._ff.res_pdg, "PS_residual.pdf"),
                       (self._ff, "PS_result.pdf")]

        for obj, name in images:
            fig, ax = plt.subplots(figsize=(16, 10))
            if isinstance(obj, LightCurve):
                obj.scatter(ax=ax)
            else:
                obj.plot(ax=ax, markersize=2)
            plt.tight_layout()
            fig.savefig(plots_path / name)
            plt.close(fig)

        if self.validation_page is not None:
            pdf_path = plots_path / "Validation_page.pdf"
            with matplotlib.backends.backend_pdf.PdfPages(pdf_path) as pdf:
                for fig in self.validation_page:
                    pdf.savefig(fig)
                    plt.close(fig)

        mprint(f"{self.label} Data saved!", info)
