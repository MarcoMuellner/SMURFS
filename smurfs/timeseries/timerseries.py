import numpy as np
from astropy.stats import LombScargle
from scipy.optimize import curve_fit
from typing import Tuple,List

from smurfs.files import saveAmpSpectrumAndImage
from smurfs.support import *

@timeit
def calculateAmplitudeSpectrum(data: np.ndarray, range: Tuple[float,float] = (0, 50)) -> np.ndarray:
    if range[0] > range[1]:
        raise ValueError("Lower frequency range must be smaller than bigger frequency range")
    ls = LombScargle(data[0],data[1],normalization='psd')
    max_frequency = range[1] if range[1] < nyquistFrequency(data) else nyquistFrequency(data)
    f,p = ls.autopower(minimum_frequency=range[0],maximum_frequency=max_frequency,samples_per_peak=100)
    p = np.sqrt(4/len(data[0]))*np.sqrt(p)
    p = p[1:len(p)]
    f = f[1:len(f)]
    p = p[f < range[1]]
    f = f[f < range[1]]
    return np.array((f,p))

@timeit
def nyquistFrequency(data: np.ndarray) -> float:
    return float(1/(2*np.mean(np.diff(data[0]))))

def findAndRemoveMaxFrequency(lightCurve: np.ndarray, ampSpectrum: np.ndarray) -> Tuple[List[float],np.ndarray]:
    maxY = max(ampSpectrum[1])
    maxX = ampSpectrum[0][abs(ampSpectrum[1] - max(ampSpectrum[1])) < 10**-4][0]

    arr = [maxY,maxX,0]

    popt,pcov = curve_fit(sin,lightCurve[0],lightCurve[1],p0 = arr)

    if popt[0] < 0:
        popt[0] = abs(popt[0])
        popt[2] += -np.pi if popt[2] > np.pi else np.pi

    retLightCurve = np.array((lightCurve[0],lightCurve[1]-sin(lightCurve[0],*popt)))

    return popt,retLightCurve

@timeit
def computeSignalToNoise(ampSpectrum: np.ndarray, windowSize: float) -> float:
    y = ampSpectrum[1]
    x = ampSpectrum[0]
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

@timeit
def recursiveFrequencyFinder(data: np.ndarray, snrCriterion: float, windowSize: float, path: str = "",
                             **kwargs):
    snr = 100
    frequencyList = []
    print(term.format("List of frequencys, amplitudes, phases, S/N",term.Color.CYAN))
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
        savePath = path+"results/"+str(int(data[0][0]))+"_"+str(int(max(data[0])))+"/"
        fileNames = "amplitude_spectrum_f_"+str(len(frequencyList))
        if saveStuff:
            saveAmpSpectrumAndImage(amp,savePath,fileNames)

    try:
        if kwargs['mode'] == 'Normal':
            saveAmpSpectrumAndImage(amp, savePath, fileNames)
    except KeyError:
        pass


    return frequencyList
