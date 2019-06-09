import pytest
from smurfs.timeseries.timerseries import *
from scipy.signal import unit_impulse
from uncertainties import unumpy as unp


def getSin(amp,frequency):
    t = np.linspace(0, 1, 1000)
    y = amp*np.sin(2*np.pi*frequency*t)
    return np.array((t,y))

testCasesFrequency = [
            (getSin(1, 5), [(1, 5)]),
            (getSin(2,10),[(2,10)]),
             (np.loadtxt("tests/testFile.dat").T,[(1.4639274842832088,47.43923486)])]

testCasesMinMax = [(getSin(1, 5), (399, 599))
            , (getSin(2,10),(899,1099))
            , (np.loadtxt("tests/testFile.dat").T,(1065229,1065474))]

testCasesSNR = [(getSin(1, 5), 8.757757597126078)
            , (getSin(2,10),9.019715823249125)
            , (np.loadtxt("tests/testFile.dat").T,25.28636173902136)]

testCasesFrequencyList = [(getSin(1, 5), 1)
            , (getSin(2,10),1)
            , (np.loadtxt("tests/testFile.dat").T,13)]

testCasesCutoffCriterion = [(np.array([0.1,0.1,0.1,0.2,0,0.3,0.2,0.1,0.2,0.5]),True),
                            (np.array([0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1]),True),
                            (np.array([0.1,10,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1]),True),
                            ]

@pytest.mark.parametrize("value", testCasesFrequency)
def test_remove_max_frequency(value):
    amp_spectrum = amplitude_spectrum(value[0])
    fit,lc = remove_max_frequency(value[0],amp_spectrum)
    fig, ax_list = pl.subplots(1, 2, figsize=(16, 10))
    fit = [i.nominal_value for i in fit]

    ax_list[0].plot(amp_spectrum[0], amp_spectrum[1], color='k', linewidth=1)
    ax_list[0].axvline(x=fit[1], linestyle='dashed', color='red')
    ax_list[1].plot(value[0][0], value[0][1], 'o', color='k', markersize=1)
    ax_list[1].plot(value[0][0], sin(value[0][0], *fit), color='red', markersize=1, alpha=0.5)
    pl.show()

@pytest.mark.parametrize("value", testCasesFrequency)
def test_find_minima(value):
    amp_spectrum = amplitude_spectrum(value[0])
    fit, lc = remove_max_frequency(value[0], amp_spectrum)
    fig,ax_list = pl.subplots(1,2,figsize=(16,10))

    fit = [i.nominal_value for i in fit]

    adjacent_minima(amp_spectrum,fit[1])

@pytest.mark.parametrize("value", testCasesFrequency)
def test_snr(value):
    amp_spectrum = amplitude_spectrum(value[0])
    fit, lc = remove_max_frequency(value[0], amp_spectrum)

    signal_to_noise(amp_spectrum,fit[1],fit[0],2)

@pytest.mark.parametrize("value", testCasesFrequency)
def test_snr(value):
    amp_spectrum = amplitude_spectrum(value[0])
    fit, lc = remove_max_frequency(value[0], amp_spectrum)

    signal_to_noise(amp_spectrum,fit[1],fit[0],2)




