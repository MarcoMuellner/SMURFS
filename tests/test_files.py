import pytest
from smurfs.files import *
from smurfs.timeseries import *

def getSin(offset,amp,frequency):
    t = np.linspace(0, 1, 2000)
    y = offset + amp*np.sin(2*np.pi*frequency*t)
    return np.array((t,y))

testCasesDataReduction = [getSin(0,1,5),
                          getSin(5,1,5),
                          getSin(0,1,5) + getSin(0,2,10),
                          np.loadtxt("tests/testFile.dat").T,
                          np.loadtxt("tests/testFile_longGaps.dat").T,
                          ]

testCasesGapTestXValues = [(np.append(np.linspace(0, 10), np.linspace(20, 30)),1/3),
                           (np.append(np.linspace(0, 5), np.linspace(15, 25)),10/25),
                           (np.linspace(0,10),0),
                           (np.append(np.linspace(0, 5), np.linspace(7, 15)), 2 / 15),
                           ]

testCasesGapValues = []
for data,ratio in testCasesGapTestXValues:
    testCasesGapValues.append((np.array((data, np.sin(data))),ratio))

testCasesGapTest = [(np.append(np.linspace(0,10),np.linspace(20,30)))]

@pytest.mark.parametrize("value",["file1","file2"])
def testReadDataFailed(value):
    with pytest.raises(IOError):
        readData(value)


def testReadData():
    data = readData("tests/testFile.dat")
    assert isinstance(data,np.ndarray)
    assert len(data) == 2

@pytest.mark.parametrize("value",testCasesDataReduction)
def testRemoveMean(value):
    data = normalizeData(value)
    assert np.mean(data[1]) < 10**-6
    assert data[0][0] == 0

@pytest.mark.parametrize("value",testCasesDataReduction)
def testGetSplits(value):
    value = normalizeData(value)
    timeRange = max(value[0])/10
    overlap = max(value[0])/50
    dataList = getSplits(value,timeRange,overlap)
    expectedLength = int((max(value[0])-timeRange)/(timeRange-overlap)) +1


    assert len(dataList) in [expectedLength,expectedLength-1,expectedLength -2]

    for i in range(0,len(dataList)-1):
        assert dataList[i+1][0][0]-max(dataList[i][0]) - overlap < 10**-3

@pytest.mark.parametrize("value",testCasesDataReduction)
def testGetSplitsMax(value):
    value = normalizeData(value)
    dataList = getSplits(value)
    assert len(dataList[0][0]) == len(value[0]) - 1

@pytest.mark.skip
@pytest.mark.parametrize("value",testCasesDataReduction)
def testWriteFile(value,tmpdir_factory):
    value = normalizeData(value)
    dataList = getSplits(value)
    dir = tmpdir_factory.mktemp('temp').join('results.txt')
    path= tmpdir_factory.mktemp('')
    result = {}
    for data in dataList:
        frequencyList = recursiveFrequencyFinder(data, 4, 2,path=path,frequencyRange=(0,50))
        result[(data[0][0], max(data[0]))] = frequencyList

    writeResults(str(dir),result)
    assert os.path.exists(str(dir))

@pytest.mark.parametrize("value", testCasesGapValues)
def testGapChecker(value):
    gapRatio = getGapRatio(value[0],0,len(value[0][0])-1)
    assert gapRatio - value[1] < 10**-5
