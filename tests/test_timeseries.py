import pytest
from smurfs.timeseries.timerseries import *


def getSin(amp,frequency):
    t = np.linspace(0, 1, 2000)
    y = amp*np.sin(2*np.pi*frequency*t)
    return np.array((t,y))

testCasesFrequency = [(getSin(1, 5), [(1, 5)])
            , (getSin(2,10),[(2,10)])
            , (np.loadtxt("tests/testFile.dat").T,[(1.4639274842832088,47.43923486)])]

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
                            (np.array([0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1]),False),
                            (np.array([0.1,10,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1]),True),
                            ]

@pytest.mark.parametrize("value", testCasesFrequency)
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

@pytest.mark.parametrize("value", testCasesFrequency)
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

@pytest.mark.parametrize("value", testCasesMinMax)
def testMinimaMaxima(value):
    data = value[0]
    checklist = value[1]
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])

    amp = calculateAmplitudeSpectrum(data)
    lowerMin,upperMin = findNextMinimas(amp[1])
    assert lowerMin == checklist[0]
    assert upperMin == checklist[1]


@pytest.mark.parametrize("value", testCasesSNR)
def testSNR(value):
    data = value[0]
    checklist = value[1]
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])

    amp = calculateAmplitudeSpectrum(data)
    _ , _ = findAndRemoveMaxFrequency(data,amp)
    snr = computeSignalToNoise(amp,2)
    assert abs(checklist - snr) < 10**-1

@pytest.mark.parametrize("value",testCasesCutoffCriterion)
def testCutoffCriterion(value):
    assert value[1] == cutoffCriterion(value[0])


def testSpectrogramCreation():
    fList = []
    tList = []
    iList = []
    with cd("tests/spectrum_files"):
        for file in os.listdir("."):
            print("Loading {0}".format(file))
            time_parts = file.split(".")[0].split("_")[-1].split("-")
            data = np.loadtxt(file).T
            f,t,i = prepareSpectrogram(data,(int(time_parts[0]),int(time_parts[0])))
            fList.append(f)
            tList.append(t)
            iList.append(i)

    print("Start plotting")

    f,t,i = combineDatasets(fList,tList,iList)
    plotMesh(f,t,i)

