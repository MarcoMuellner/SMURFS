import numpy as np
from astropy.stats import LombScargle
from scipy.optimize import curve_fit
from typing import Tuple, List

from smurfs.support import *
from uncertainties import ufloat
from smurfs.support.config import conf, UncertaintyMode


def spectral_window(data: np.ndarray, frequencyBoundary: Tuple[float, float] = (0, 50)) -> np.ndarray:
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
    num = integer_min if integer_min * (frequencyBoundary[1] - frequencyBoundary[0]) < integer_min else integer_min * (
                frequencyBoundary[1] - frequencyBoundary[0])
    f = np.linspace(frequencyBoundary[0], frequencyBoundary[1], num=num)

    if max(len(t), len(f)) > 1000:
        p = np.abs([(1 / len(t)) * np.sum(2 * np.pi * 1j * i * t) for i in f])
    else:
        p = np.abs(1 / len(t) * np.sum(2 * np.pi * 1j * np.outer(t, f), axis=0))

    return np.array((f, p))


@timeit
def amplitude_spectrum(data: np.ndarray, frequencyBoundary: Tuple[float, float] = None) -> np.ndarray:
    """
    This function computes a periodogram using the LombScargle algorithm. There are different implementations available
    and we leave it up to astropy to decide which one should be applied
    :param data: Temporal dataset, an observation by some kind instrument. First axis time, second axis flux
    :param frequencyBoundary: Boundary that should be considered when computing the spectrum
    :return: 2-D Array, containing frequency (first array) and amplitude (second array)
    """
    if frequencyBoundary == None:
        frequencyBoundary = (0, nyquistFrequency(data))

    if frequencyBoundary[0] > frequencyBoundary[1]:
        raise ValueError(b"f_min has to be smaller than f_max!")

    # create object
    indx = np.isfinite(data[1])
    ls = LombScargle(data[0][indx], data[1][indx], center_data=True)

    # if defined max frequency is bigger than the nyquist frequency, cutoff at nyquist
    nFrequency = nyquistFrequency(data)
    if frequencyBoundary[1] > nFrequency:
        print(term.format("Upper Frequencyrange of {0} is higher than Nyquist frequency. Please be aware that "
                          "this can lead to problems with the results!"
                          .format(frequencyBoundary[1], nyquistFrequency), term.Color.YELLOW))

    max_frequency = frequencyBoundary[1]

    # compute Spectrum
    # power = ls.power(freq, normalization='psd', method='fast', assume_regular_frequency=True)
    f, p = ls.autopower(minimum_frequency=frequencyBoundary[0], maximum_frequency=max_frequency, normalization='psd',
                        method='fast')

    # use only finite values
    indx = np.isfinite(p)
    p = p[indx]
    f = f[indx]

    # Normalization according to parcivals theorem
    N = len(ls.t)
    tot_MS = np.sum((ls.y - np.mean(ls.y)) ** 2) / N
    tot_lomb = np.sum(p)
    normfactor = tot_MS / tot_lomb
    p = np.sqrt(p * normfactor)

    removeSectors = conf().removeSector

    for (lower, upper) in removeSectors:
        tmpArray = p[f < lower]
        p = np.append(tmpArray, p[f > upper])

        tmpArray = f[f < lower]
        f = np.append(tmpArray, f[f > upper])
    # restricting values to upper boundary
    p = p[f < frequencyBoundary[1]]
    f = f[f < frequencyBoundary[1]]

    return np.array((f, p))


@timeit
def nyquistFrequency(data: np.ndarray) -> float:
    """
    Computes Nyquist frequency.
    :param data: Dataset, in time domain.
    :return: Nyquist frequency of dataset
    """
    indx = np.isfinite(data[1])
    return float(1 / (2 * np.median(np.diff(data[0][indx]))))


def sin(x: np.ndarray, amp: float, f: float, phase: float) -> np.ndarray:
    return amp * np.sin(2 * np.pi * f * x + phase)


def max_f(amp_spectrum: np.ndarray) -> Tuple[float, float]:
    y = max(amp_spectrum[1])
    x = amp_spectrum[0][np.argsort(np.abs(amp_spectrum[1] - np.amax(amp_spectrum[1])))[0]]
    return x, y


def remove_max_frequency(light_curve: np.ndarray, amp_spectrum: np.ndarray) -> Tuple[List[float], np.ndarray]:
    """
    Finds the frequency with maximum power in the spectrum, fits it to the dataset and than removes this frequency
    from the initial dataset.
    :param lightCurve: Lightcurve dataset. This is the data where the fit is applied to, and its removed version is
    returned
    :param ampSpectrum: Amplitude spectrum of lightCurve. Should be computed with the same dataset that is provided here
    :return: Fit parameters, Reduced lightcurve
    """
    x, y = max_f(amp_spectrum)

    return remove_frequency(light_curve, x, y)


def remove_frequency(light_curve: np.ndarray, f: float, amp: float) -> Tuple[List, np.ndarray]:
    arr = [amp, f, 0]
    bounds = [[0, 0, 0], [np.inf, np.inf, 2 * np.pi]]

    for i in range(0, 3):
        try:
            popt, pcov = curve_fit(sin, light_curve[0], light_curve[1], p0=arr, bounds=bounds)
        except RuntimeError:
            print(term.format("Failed to find a good fit for Frequency " + str(f) + "c/d", term.Color.RED))
            raise RuntimeError

        if defines.minimumIntensity is None or defines.minimumIntensity > popt[0]:
            defines.minimumIntensity = popt[0]

        perr = np.sqrt(np.diag(pcov))

        ret = []
        if conf().uncertaintiesMode == UncertaintyMode.montgomery.value:
            # computation of uncertainties with Montgomery & O'Donoghue (1999)
            sigma_m = np.std(light_curve[1])
            sigma_amp = np.sqrt(2 / len(light_curve[1])) * sigma_m
            sigma_f = np.sqrt(6 / len(light_curve[1])) * (
                        1 / (np.pi * max(light_curve[0]) - min(light_curve[0]))) * sigma_m / popt[0]
            sigma_phi = np.sqrt(2 / len(light_curve[1])) * sigma_m / popt[0]
            ret = [
                ufloat(popt[0], sigma_amp),
                ufloat(popt[1], sigma_f),
                ufloat(popt[2], sigma_phi)
            ]
        else:
            for i in range(0, len(popt)):
                ret.append(ufloat(popt[i], perr[i]))

        arr = popt

    ret_lc = light_curve[1] - sin(light_curve[0], *popt)

    return ret, np.array((light_curve[0], ret_lc))


def findMaxPowerFrequency(ampSpectrum: np.ndarray):
    maxY = max(ampSpectrum[1])
    maxX = ampSpectrum[0][np.argsort(np.abs(ampSpectrum[1] - np.amax(ampSpectrum[1])))[0]]

    return maxY, maxX


def adjacent_minima(amp_spectrum: np.ndarray, f: float) -> Tuple[int, int]:
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

    return lower, upper


def signal_to_noise_max_f(amp_spectrum: np.ndarray, window_size: float) -> float:
    x, y = max_f(amp_spectrum)
    return signal_to_noise(amp_spectrum, x, y, window_size)


def signal_to_noise(amp_spectrum: np.ndarray, f: float, amp: float, window_size: float) -> float:
    lower, upper = adjacent_minima(amp_spectrum, f)

    df = np.mean(np.diff(amp_spectrum[0]))
    points = int(window_size // df)

    noise = np.mean(np.hstack((amp_spectrum[1][lower - points:lower], amp_spectrum[1][upper:upper + points])))
    return float(amp / noise)


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

    lowerIndex = 0 if len(fList) < similarFrequenciesCount else len(fList) - similarFrequenciesCount
    upperIndex = len(fList) - 1
    lastFrequencies = np.array(fList[lowerIndex:upperIndex])
    stdDev = lastFrequencies.std()
    if stdDev < similarityStdDev and not conf().skipCutoff:
        print(
            term.format("The last " + str(similarFrequenciesCount) + " where to similar, with a standard deviation of "
                        + str(stdDev), term.Color.RED))
        if conf().skipSimilarFrequencies:
            conf().removeSector.append((lastFrequencies.mean() - 10 * stdDev, lastFrequencies.mean() + 10 * stdDev))
            print(term.format(f"Ignoring from {conf().removeSector[-1][0]} to {conf().removeSector[-1][1]}",
                              term.Color.RED))
            return True
        else:
            print(term.format(f"Ending this sector", term.Color.RED))
            return False
    else:
        return True
