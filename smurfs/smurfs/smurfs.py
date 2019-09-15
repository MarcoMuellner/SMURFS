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
from smurfs.smurfs.frequency_finder import FFinder, sin_multiple
from smurfs.signal.periodogramm import Periodogram
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
    def __init__(self, file=None, time=None, flux=None, target_name=None, flux_type='PDCSAP', label=None, quiet_flag=False):
        mpr.quiet = quiet_flag
        if target_name is not None:
            self.lc: TessLightCurve = download_lc(target_name, flux_type)
            if label is None:
                self.label = target_name
            else:
                self.label = label
        elif time is None and flux is None and file is None:
            raise AttributeError(ctext("You need to either pass a file path or time and flux of the lightcurve object",error))
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
            raise AttributeError(ctext("You need to either pass a file path or time and flux of the lightcurve object"))

        self.pdg: Periodogram = Periodogram.from_lightcurve(self.lc)
        self.result = df([], columns=['f_obj', 'frequency', 'amp', 'phase', 'snr', 'res_noise', 'significant'])
        self.combinations = df([],
                               columns=["Name", "ID", "Frequency", "Amplitude", "Solution", "Residual", "Independent",
                                        "Other_Solutions"])
        self.ff: FFinder = None
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
    def settings(self):
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
        columns = ['Duty cycle',
                   'Nyquist frequency',
                   'Total number of found frequencies']
        return df([[self.duty_cycle, self.nyquist, len(self.result)]], columns=columns)

    @property
    def obs_length(self):
        return self.lc.time[-1] - self.lc.time[0]

    @property
    def nyquist(self):
        return 1 / (2 * np.median(np.diff(self.lc.time)))

    @property
    def duty_cycle(self):
        diff = np.diff(self.lc.time)
        t = np.median(diff)
        std = np.std(diff)
        mask = diff > (t + 3 * std)
        return (1 - np.sum(diff[mask]) / np.sum(diff))

    @property
    def periodogramm(self):
        return self.pdg

    @property
    def spectral_window(self):
        """
        Computes the spectral window of a given dataset. Derivation of formula from Asteroseismology (2010).
        :return: FFT of window
        """
        if self._spectral_window is None:
            spec_lc = self.lc.copy()
            spec_lc.flux = np.zeros(len(self.lc.flux)) + 1
            self._spectral_window = Periodogram.from_lightcurve(spec_lc)
        return self._spectral_window

    def fold(self, period, t0=None, transit_midpoint=None):
        return self.lc.fold(period, t0, transit_midpoint)

    def flatten(self, window_length=101, polyorder=2, return_trend=False, break_tolerance=5, niters=3, sigma=3,
                mask=None, **kwargs):
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
            mode='scipy'):

        self.snr = snr
        self.window_size = window_size
        self.f_min = f_min
        self.f_max = f_max
        self.skip_similar = skip_similar
        self.similar_chanel = similar_chancel
        self.extend_frequencies = 0

        self.ff = FFinder(self, f_min, f_max)
        self.result = self.ff.run(snr=snr, window_size=window_size, skip_similar=skip_similar,
                                  similar_chancel=similar_chancel
                                  , extend_frequencies=extend_frequencies,improve_fit=improve_fit,mode=mode)
        self.combinations = get_combinations(self.result.index.tolist(),
                                             unp.nominal_values(self.result.frequency.tolist())
                                             , unp.nominal_values(self.result.amp.tolist()))

    def plot_lc(self, show=False, **kwargs):
        for i in ['color','ylabel','normalize']:
            try:
                del kwargs[i]
            except KeyError:
                pass

        ax : Axes = self.lc.scatter(color='k', ylabel="Flux [mag]",normalize=False, **kwargs)
        if len(self.result) > 0:
            params = []

            for i,j,k in zip(self.result.amp,self.result.frequency,self.result.phase):
                params.append(i.nominal_value)
                params.append(j.nominal_value)
                params.append(k.nominal_value)

            y = sin_multiple(self.lc.time,*params)
            ax.plot(self.lc.time,y,color='red',linewidth=1)
        if show:
            pl.show()

    def plot_pdg(self, show=False, plot_insignificant=False, **kwargs):
        if self.ff is None:
            self.pdg.plot(color='k', **kwargs)
        else:
            self.ff.plot(show=show, plot_insignificant=plot_insignificant, **kwargs)

    def interact_bls(self, notebook_url='localhost:8888', minimum_period=None, maximum_period=None, resolution=2000):
        return self.lc.interact_bls(notebook_url, minimum_period, maximum_period, resolution)

    def save(self, path: str, store_obj=False):
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
                if self.result is not None:
                    frame: df = self.result.drop(columns=['f_obj'])
                    frame.index.name = 'f_nr'
                    df_list = [(self.settings, '#Settings'),
                               (self.statistics, '#Statistics'),
                               (frame, '#Result')]

                    with open('result.csv', 'w') as f:
                        for fr, comment in df_list:
                            f.write(f"{comment}\n")
                            fr.to_csv(f)
                            f.write("\n\n")

                    self.combinations.to_csv('combinations.csv')

                self.lc.to_csv("LC.txt")
                self.pdg.to_csv("PS.txt")
                if self.ff is not None:
                    self.ff.res_lc.to_csv("LC_residual.txt")
                    self.ff.res_pdg.to_csv("PS_residual.txt")

                if store_obj:
                    pickle.dump(self, open("obj.smurfs", "wb"))

            with cd("plots"):
                images = [(self.lc, "LC.pdf"),
                          (self.pdg, "PS.pdf"),
                          ]

                if self.ff is not None:
                    images += [(self.ff.res_lc, "LC_residual.pdf"),
                               (self.ff.res_pdg, "PS_residual.pdf"),
                               (self.ff, "PS_result.pdf")
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
        mprint("Done!", info)
