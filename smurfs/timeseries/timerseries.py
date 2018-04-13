import numpy as np
from astropy.stats import LombScargle
from scipy.optimize import curve_fit
from typing import Tuple,List

from smurfs.files import saveAmpSpectrumAndImage
from smurfs.support import *

@timeit
def calculateAmplitudeSpectrum(data: np.ndarray, frequencyBoundary: Tuple[float, float] = (0, 50)) -> np.ndarray:
    """
    This function computes a periodogram using the LombScargle algorithm. There are different implementations available
    and we leave it up to astropy to decide which one should be applied
    :param data: Temporal dataset, an observation by some kind instrument. First axis time, second axis flux
    :param frequencyBoundary: Boundary that should be considered when computing the spectrum
    :return: 2-D Array, containing frequency (first array) and amplitude (second array)
    """
    if frequencyBoundary[0] > frequencyBoundary[1]:
        raise ValueError(b"f_min has to be smaller than f_max!")

    #create object
    ls = LombScargle(data[0],data[1],normalization='psd')

    # if defined max frequency is bigger than the nyquist frequency, cutoff at nyquist
    max_frequency = frequencyBoundary[1] if frequencyBoundary[1] < nyquistFrequency(data) else nyquistFrequency(data)

    #compute Spectrum
    f,p = ls.autopower(minimum_frequency=frequencyBoundary[0], maximum_frequency=max_frequency, samples_per_peak=100)

    #normalization of psd in order to get good amplitudes
    p = np.sqrt(4/len(data[0]))*np.sqrt(p)

    #removing first item
    p = p[1:]
    f = f[1:]

    #restricting values to upper boundary
    p = p[f < frequencyBoundary[1]]
    f = f[f < frequencyBoundary[1]]

    return np.array((f,p))

@timeit
def nyquistFrequency(data: np.ndarray) -> float:
    """
    Computes Nyquist frequency.
    :param data: Dataset, in time domain.
    :return: Nyquist frequency of dataset
    """
    return float(1/(2*np.mean(np.diff(data[0]))))

def findMaxPowerFrequency(ampSpectrum: np.ndarray):
    maxY = max(ampSpectrum[1])
    maxX = ampSpectrum[0][abs(ampSpectrum[1] - max(ampSpectrum[1])) < 10 ** -4][0]

    return maxY,maxX

def findAndRemoveMaxFrequency(lightCurve: np.ndarray, ampSpectrum: np.ndarray) -> Tuple[List[float],np.ndarray]:
    """
    Finds the frequency with maximum power in the spectrum, fits it to the dataset and than removes this frequency
    from the initial dataset.
    :param lightCurve: Lightcurve dataset. This is the data where the fit is applied to, and its removed version is
    returned
    :param ampSpectrum: Amplitude spectrum of lightCurve. Should be computed with the same dataset that is provided here
    :return: Fit parameters, Reduced lightcurve
    """
    maxY,maxX = findMaxPowerFrequency(ampSpectrum)
    popt = [-1,-1,-1]
    arr = [maxY, maxX, 0]

    # First fit could provide negative values for amplitude and frequency if the phase is moved by pi. Therefore run
    # again, with phase moved by pi as long as we don't have positive values for freuqency and amplitude
    while popt[0] < 0 or popt[1] < 0:
        try:
            popt,pcov = curve_fit(sin,lightCurve[0],lightCurve[1],p0 = arr)
        except RuntimeError:
            print(term.format("Failed to find a good fit for Frequency "+str(maxX)+"c/d",term.Color.RED))
            raise RuntimeError



        #if amp < 0 -> move sin to plus using the phase by adding pi
        if popt[0] < 0 or popt[1] < 0:
            popt[0] = abs(popt[0])
            popt[1] = abs(popt[1])
            popt[2] += -np.pi if popt[2] > np.pi else np.pi
        arr = popt

        retLightCurve = np.array((lightCurve[0],lightCurve[1]-sin(lightCurve[0],*popt)))

    return popt,retLightCurve

@timeit
def computeSignalToNoise(ampSpectrum: np.ndarray, windowSize: float) -> float:
    """
    Computes signal to noise ratio at frequency f.
    :param ampSpectrum:
    :param windowSize:
    :return:
    """
    y = ampSpectrum[1]
    x = ampSpectrum[0]

    #find minimas adjacent to maxima of y
    lowerMinima,upperMinima = findNextMinimas(y)
    singleStep = np.mean(np.diff(x))
    length_half = int(windowSize/singleStep)

    data = np.append(y[lowerMinima - length_half:lowerMinima],y[upperMinima:upperMinima+length_half])
    meanValue = np.mean(data)
    maxVal = y[abs(y - max(y)) < 10**-6][0]

    return float(maxVal/meanValue)

@timeit
def findNextMinimas(yData: np.ndarray) -> Tuple[int,int]:
    index = int(np.where(abs(yData - max(yData)) < 10**-6)[0][0])
    minimaFound = False
    counter = 1
    lowerMinima = 0
    upperMinima = 0
    while(minimaFound == False):
        negCounter = index - counter
        posCounter = index + counter
        if checkMinima(yData,negCounter):
            lowerMinima = negCounter
        if checkMinima(yData,posCounter):
            upperMinima = posCounter

        if lowerMinima != 0 and upperMinima != 0:
            minimaFound = True
        counter += 1

    return lowerMinima,upperMinima


def checkMinima(yData: np.ndarray, counter: int) -> bool:
    return yData[counter] < yData[counter + 1] and yData[counter] < yData[counter- 1]


def sin(x: np.ndarray, amp:float, f: float, phase: float) -> np.ndarray:
    return amp * np.sin(2*np.pi * f * x + phase)

def cutoffCriterion(frequencyList:List):
    if len(frequencyList) < similarFrequenciesCount:
        return True

    lastFrequencies = np.array(frequencyList[-similarFrequenciesCount:])
    stdDev = lastFrequencies.std()
    if stdDev < similarityStdDev:
        print(term.format("The last "+str(similarFrequenciesCount)+" where to similar, with a standard deviation of "
                          +str(stdDev)+". Stopping analysis for this set",term.Color.RED))
        return False
    else:
        return True


@timeit
def recursiveFrequencyFinder(data: np.ndarray, snrCriterion: float, windowSize: float, path: str = "",
                             **kwargs):
    try:
        snr = 100
        frequencyList = []
        print(term.format("List of frequencys, amplitudes, phases, S/N",term.Color.CYAN))
        savePath = path + "results/{0:0=3d}".format(int(data[0][0]))
        savePath += "_{0:0=3d}/".format(int(max(data[0])))

        while(snr > snrCriterion):
            try:
                frequencyList.append((fit[1],snr,fit[0],fit[2],))
                saveStuff = True if kwargs['mode'] == 'Full' else False
            except:
                saveStuff = True
            amp = calculateAmplitudeSpectrum(data,kwargs['frequencyRange'])
            snr = computeSignalToNoise(amp, windowSize)
            fit,data = findAndRemoveMaxFrequency(data,amp)

            print(term.format(str(fit[1])+"c/d     "+str(fit[0])+"     "+str(fit[2])+"    "+str(snr), term.Color.CYAN))

            fileNames = "amplitude_spectrum_f_"+str(len(frequencyList))

            if saveStuff:
                saveAmpSpectrumAndImage(amp,savePath,fileNames)

            if not cutoffCriterion(frequencyList):
                break


        try:
            if kwargs['mode'] == 'Normal':
                saveAmpSpectrumAndImage(amp, savePath, fileNames)
        except KeyError:
            pass
    except KeyboardInterrupt:
        print(term.format("Interrupted Run",term.Color.RED))
        defines.dieGracefully = True
        return frequencyList


    return frequencyList
