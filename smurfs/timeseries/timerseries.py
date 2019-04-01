import numpy as np
from astropy.stats import LombScargle
from scipy.optimize import curve_fit
from scipy.signal.windows import get_window
from typing import Tuple, List, Dict
import warnings

from smurfs.files import saveAmpSpectrumAndImage,save_frequency_spacing,getMostCommonStep
from smurfs.support import *
from uncertainties import ufloat
from smurfs.support.config import conf,UncertaintyMode
from scipy.integrate import simps

def spectral_window(data:np.ndarray, frequencyBoundary: Tuple[float, float] = (0, 50)) -> np.ndarray:
    """
    Computes the spectral window of a given dataset. Derivation of formula from Asteroseismology (2010)
    :param data: time series dataset
    :param frequencyBoundary: boundaries for spectral window
    :return: FFT of window
    """
    if len(data) != 2:
        raise ValueError("Please move the whole dataset through!")

    t = data[0]
    integer_min = 200
    num = integer_min if integer_min*(frequencyBoundary[1]-frequencyBoundary[0]) < integer_min else integer_min*(frequencyBoundary[1]-frequencyBoundary[0])
    f = np.linspace(frequencyBoundary[0],frequencyBoundary[1] , num=num)

    if max(len(t),len(f)) > 1000 :
        p = np.abs([(1 / len(t)) * np.sum(2 * np.pi * 1j * i * t) for i in f])
    else:
        p = np.abs( 1 / len(t) * np.sum(2 * np.pi * 1j * np.outer(t, f), axis=0))

    return np.array((f,p))

def window_function(df,nyq,ls = None,width = None, oversampling = 10):
    if width is None:
        width = 100 * df

    freq_cen = 0.5 * nyq

    Nfreq = None

    while Nfreq == None:
        Nfreq = int(oversampling * width / df)
        freq = freq_cen + (df / oversampling) * np.arange(-Nfreq, Nfreq, 1)
        if np.amin(freq) < 0:
            Nfreq = None
            width *= 0.5

    x = 0.5 * np.sin(2 * np.pi * freq_cen * ls.t) + 0.5 * np.cos(2 * np.pi * freq_cen * ls.t)

    # Calculate power spectrum for the given frequency range:
    ls = LombScargle(ls.t, x, center_data=True)
    power = ls.power(freq, method='fast', normalization='psd', assume_regular_frequency=True)
    power /= power[int(len(power) / 2)]  # Normalize to have maximum of one

    freq -= freq_cen
    return freq, power

def fundamental_spacing_integral(df,nyq,ls):
    freq, window = window_function(df,nyq,ls,width=100*df, oversampling=5)
    df = simps(window, freq)
    return df


def amplitude_spectrum(data: np.ndarray, frequencyRange = None) -> np.ndarray:
    """
    Computes a given periodogram from the lightcurve
    :param data: Lightcurve dataset
    :return: Periodogram from the dataset
    """
    indx = np.isfinite(data[1])
    df = 1 / (np.amax(data[0][indx]) - np.amin(data[0][indx]))  # Hz
    ls = LombScargle(data[0][indx], data[1][indx], center_data=True)
    nyq = nyquistFrequency(data)

    df = fundamental_spacing_integral(df,nyq,ls)

    freq = np.arange(df ,nyq, df)
    power = ls.power(freq, normalization='psd', method='fast', assume_regular_frequency=True)

    N = len(ls.t)
    tot_MS = np.sum((ls.y - np.mean(ls.y)) ** 2) / N
    tot_lomb = np.sum(power)
    normfactor = tot_MS / tot_lomb
    power = np.sqrt(power * normfactor)

    if frequencyRange is not None and len(frequencyRange) == 2:
        power = power[np.logical_and(freq > frequencyRange[0], freq < frequencyRange[1])]
        freq = freq[np.logical_and(freq > frequencyRange[0], freq < frequencyRange[1])]

    return np.array((freq,power))


@timeit
def nyquistFrequency(data: np.ndarray) -> float:
    """
    Computes Nyquist frequency.
    :param data: Dataset, in time domain.
    :return: Nyquist frequency of dataset
    """
    indx = np.isfinite(data[1])
    return float(1/(2*np.median(np.diff(data[0][indx]))))

def sin(x: np.ndarray, amp: float, f: float, phase: float) -> np.ndarray:
    return amp * np.sin(2 * np.pi * f * x + phase)

def remove_max_frequency(light_curve : np.ndarray, amp_spectrum : np.ndarray) -> Tuple[List[float],np.ndarray]:
    """
    Finds the frequency with maximum power in the spectrum, fits it to the dataset and than removes this frequency
    from the initial dataset.
    :param lightCurve: Lightcurve dataset. This is the data where the fit is applied to, and its removed version is
    returned
    :param ampSpectrum: Amplitude spectrum of lightCurve. Should be computed with the same dataset that is provided here
    :return: Fit parameters, Reduced lightcurve
    """
    y = max(amp_spectrum[1])
    x = amp_spectrum[0][np.argsort(np.abs(amp_spectrum[1] - np.amax(amp_spectrum[1])))[0]]

    return remove_frequency(light_curve,x,y)

def remove_frequency(light_curve : np.ndarray, f : float, amp : float) -> Tuple[List,np.ndarray]:
    arr = [amp,f,0]
    bounds = [[0,0,0],[np.inf,np.inf,2*np.pi]]

    try:
        popt, pcov = curve_fit(sin, light_curve[0], light_curve[1], p0=arr,bounds=bounds)
    except RuntimeError:
        print(term.format("Failed to find a good fit for Frequency " + str(f) + "c/d", term.Color.RED))
        raise RuntimeError

    if defines.minimumIntensity is None or defines.minimumIntensity > popt[0]:
        defines.minimumIntensity = popt[0]

    perr = np.sqrt(np.diag(pcov))

    ret = []

    if conf().uncertaintiesMode == UncertaintyMode.fit.value:
        for i in range(0,len(popt)):
            ret.append(ufloat(popt[i],perr[i]))
    elif conf().uncertaintiesMode == UncertaintyMode.montgomery.value:
        #computation of uncertainties with Montgomery & O'Donoghue (1999)
        sigma_m = np.std(light_curve[1])
        sigma_amp = np.sqrt(2/len(light_curve[1])) * sigma_m
        sigma_f = np.sqrt(6/len(light_curve[1])) * (1/(np.pi*max(light_curve[0])-min(light_curve[0]))) * sigma_m/popt[0]
        sigma_phi = np.sqrt(2/len(light_curve[1])) * sigma_m/popt[0]
        ret = [
            ufloat(popt[0],sigma_amp),
            ufloat(popt[1],sigma_f),
            ufloat(popt[2],sigma_phi)
        ]
    elif conf().uncertaintiesMode == UncertaintyMode.none.value:
        for i in popt:
            ret.append(ufloat(i,0))
    else:
        raise ValueError(f"Unknown error computation with {conf().uncertaintiesMode}")

    ret_lc = light_curve[1] - sin(light_curve[0],*popt)

    return ret, np.array((light_curve[0],ret_lc))

def adjacent_minima(amp_spectrum : np.ndarray,f : float) -> Tuple[int,int]:
    x = amp_spectrum[0]
    y = amp_spectrum[1]

    idx = np.argsort(np.abs(amp_spectrum[0] - f))[0]

    extrema = np.diff(np.sign(np.diff(y)))

    ids = np.sort(np.abs(np.argwhere(extrema < 0).T - idx))

    try:
        lower = ids[ids < idx][::-1][0]
    except IndexError:
        lower = 0
    try:
        upper = ids[ids > idx][0]
    except IndexError:
        upper = len(x)

    return lower,upper

def signal_to_noise(amp_spectrum : np.ndarray, f : float, amp : float, window_size : float):
    lower,upper = adjacent_minima(amp_spectrum,f)

    df = np.mean(np.diff(amp_spectrum[0]))
    points = int(window_size//df)

    noise = np.mean(np.hstack((amp_spectrum[1][lower-points:lower],amp_spectrum[1][upper:upper+points])))
    return amp/noise

def cutoffCriterion(frequencyList: List):
    if len(frequencyList) < similarFrequenciesCount:
        return True
    fList = []

    for i in frequencyList:
        try:
            fList.append(i[0].nominal_value)
        except IndexError:
            try:
                fList.append(i.nominal_value)
            except AttributeError:
                fList.append(i)

    lowerIndex = 0 if len(fList)<similarFrequenciesCount else len(fList)-similarFrequenciesCount
    upperIndex = len(fList)-1
    lastFrequencies = np.array(fList[lowerIndex:upperIndex])
    stdDev = lastFrequencies.std()
    if stdDev < similarityStdDev and not conf().skipCutoff:
        print(
            term.format("The last " + str(similarFrequenciesCount) + " where to similar, with a standard deviation of "
                        + str(stdDev), term.Color.RED))
        if conf().skipSimilarFrequencies:
            conf().removeSector.append((lastFrequencies.mean()-10*stdDev,lastFrequencies.mean()+10*stdDev))
            print(term.format(f"Ignoring from {conf().removeSector[-1][0]} to {conf().removeSector[-1][1]}",term.Color.RED))
            return True
        else:
            print(term.format(f"Ending this sector",term.Color.RED))
            return False
    else:
        return True


def find_frequencies(data : np.ndarray, snr_cutoff : float, window_size : float):
    snr = None
    lc_res = data

    n = 1

    while snr == None or snr > snr_cutoff:
        amp_spectrum = amplitude_spectrum(lc_res)
        fit, lc_res = remove_max_frequency(lc_res,amp_spectrum)
        snr = signal_to_noise(amp_spectrum,fit[1],fit[0],window_size)
        print(term.format(
            "F" + str(n) + "  " + str(fit[1]) + "c/d     " + str(fit[0]) + "     " + str(fit[2]) + "    " + str(snr),
            term.Color.CYAN))
        n+=1