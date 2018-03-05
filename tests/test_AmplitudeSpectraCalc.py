import pytest
from amplitude_spectra_calculation import *
import pylab as pl

def getSin(amp,frequency):
    t = np.linspace(0, 1, 2000)
    y = amp*np.sin(2*np.pi*frequency*t)
    return np.array((t,y))

testCases = [(getSin(1,5),[(1,5)])
            ,(getSin(2,10),[(2,10)])
            ,(np.loadtxt("betaPic_BTrBHr_all_2col.dat").T,[(1.4639274842832088,47.43923486)])]

#@pytest.mark.parametrize("value",testCases)
@pytest.mark.skip(reason="debug")
def testCalculateAmplitudeSpectrum(value):
    data = value[0]
    checklist = value[1]
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])
    amp = calculateAmplitudeSpectrum(data)
    for (a,f) in checklist:
        xData = amp[0][abs(amp[0] - f) < 10**-3]
        assert len(xData) != 0
        yData = amp[1][abs(amp[0] - f) < 10**-3]
        assert yData[0] - a < 10**-1
        print(yData[0])
    print("Max amp: "+str(np.amax(amp[1][1:len(amp[1])])))
    print("Max f: "+ str(amp[0][amp[1] == max(amp[1])]))

#@pytest.mark.parametrize("value",testCases)
@pytest.mark.skip(reason="debug")
def testFit(value):
    data = value[0]
    checklist = value[1]
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])

    amp = calculateAmplitudeSpectrum(data)
    fit,data = findAndRemoveMaxFrequency(data,amp)

    for (a,f) in checklist:
        assert fit[0] - a < 10**-4
        assert fit[1] - f < 10**-4

#@pytest.mark.parametrize("value",testCases)
@pytest.mark.skip(reason="debug")
def testMinimaMaxima(value):
    data = value[0]
    checklist = value[1]
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])

    amp = calculateAmplitudeSpectrum(data)
    lowerMin,upperMin = findNextMinimas(amp[1])


#@pytest.mark.parametrize("value",testCases)
@pytest.mark.skip(reason="debug")
def testSNR(value):
    data = value[0]
    checklist = value[1]
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])

    amp = calculateAmplitudeSpectrum(data)
    fit,data = findAndRemoveMaxFrequency(data,amp)
    snr = computeSignalToNoise(amp,2)
    print(snr)

@pytest.mark.parametrize("value",testCases)
def testRecursiveStuff(value):
    data = value[0]
    checklist = value[1]
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])

    recursiveFrequencyFinder(data,4,2)

