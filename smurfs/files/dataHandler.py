import numpy as np
from smurfs.support import *
import warnings
with warnings.catch_warnings():
    from plotnine import *
from typing import List,Dict,Tuple
from collections import OrderedDict

@timeit
def normalizeData(data: np.ndarray) -> np.ndarray:
    """
    This function reduces the dataset to make computations easier. It subtracts the 0 point in the temporal axis and
    removes the mean of the dataset.
    :param data: The dataset, probably read through readData
    :return: A normalized dataset
    """
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])
    return data

@timeit
def readFrequencyMarker(file: str) -> Dict[str,float]:
    """
    Reads frequency Marker from file. First column needs to be the name of the marker, the second column needs to have
    the according frequency value for the marker.
    :param file: File where the marker are stored.
    :return: dict containing the dataset
    """
    if not isinstance(file,str):
        raise AttributeError("Parameter file is not a string! It is type {0}".format(type(file)))

    if not os.path.exists(file):
        raise FileNotFoundError("File {0} was not found!".format(file))

    marker = OrderedDict()
    with open(file,'r') as f:
        for line in f:
            try:
                name, value = str(line).split("\t")
            except ValueError:
                raise IOError("File {0} has not two ""columns! Needs to have only two. Has {1} "
                              "column".format(file,str(line).split("\t")))
            marker[name] = float(value)

    return marker
    pass

@timeit
def readData(file: str) -> np.ndarray:
    """
    This function checks if the filepath in file exists (if not it raises an IOError) and than reads the file into
    a numpy array
    :param file The filepath to the file which is to be read:
    :return Returns the array containing the data of file:
    """
    if not os.path.exists(file):
        raise IOError("File " + os.getcwd()+"/"+file + " doesn't exist!")

    return np.loadtxt(file).T

@timeit
def getSplits(data: np.ndarray, timeRange: float = -1, overlap: float = 0,ignoreCutoffRatio : bool = False) -> List[np.ndarray]:
    """
    The getSplits function creates equally sized chunks of the original dataset with an optional overlap between two
    chunks and returns a list of these arrays. To do this, it finds the nearest index to a datapoint which responds to
    the timeRange and slices the array accordingly.
    :param data: The dataset which is to be cut up
    :param timeRange:  The timeRange for one chunk. For example if overlap is 0 and timeRange is 50, the chunks will
    have the size of 0->50,50-100,...
    :param overlap: The overlap between two chunks. For example if overlap is 2 and timeRange is 50, the chunks will
    have the size of 0->50,48->95,...
    :return: A list of chunks of the original data
    """
    if data[0][0] != 0:
        data = normalizeData(data)

    if timeRange == -1:
        timeRange = max(data[0])
    dataPoints = []
    i = 0
    while(i*(timeRange-overlap)+timeRange <= max(data[0])):
        lowerIndex = find_nearest(data[0],i*(timeRange-overlap))
        upperIndex = find_nearest(data[0],i*(timeRange-overlap)+timeRange)+1

        #this case can happen, if the full range is used, and no overlap is present
        if upperIndex == len(data[0]):
            upperIndex -= 1

        i += 1
        if timeRange != max(data[0]):
            gapRatio= getGapRatio(data,lowerIndex,upperIndex)
            if gapRatio > cutoffRatio:
                if not ignoreCutoffRatio:
                    print(term.format("Ignoring time base from "+str(int(data[0][lowerIndex]))+" to "+str(int(data[0][upperIndex]))+
                                      " because the gap Ratio is greater 0.5. Gap Ratio is "+str(gapRatio),term.Color.RED))
                    continue
                else:
                    print(term.format("Time base from  " + str(int(data[0][lowerIndex])) + " to " + str(
                        int(data[0][upperIndex])) +" has a gap ratio of  " + str(gapRatio) +
                          ", but will be taken eitherway because of ignoreCutoffRatio=True",term.Color.YELLOW))
        else:
            print(term.format("Ommited gap ratio. Time Range is "+str(timeRange)+",max data "+str(max(data[0])),term.Color.CYAN))
        array = np.array((data[0][lowerIndex:upperIndex],data[1][lowerIndex:upperIndex]))
        dataPoints.append(array)

    return dataPoints

def getMostCommonStep(data: np.ndarray):
    (values, counts) = np.unique(np.diff(data[0]), return_counts=True)
    ind = np.argmax(counts)
    return ind,values

@timeit
def getGapRatio(data: np.ndarray, lowerIndex:int, upperIndex:int):
    """
    Calculates the ratio between the "empty" space within a given dataset to its datapoints. For example
    an array containing the datapoints 0,1,2,3,7,8,9 would return 0.3 as gap ratio, as one third of the data is not
    populated. To do this, it calculates the most common difference between two points, and sums up deviations for gaps
    bigger than this value.
    :param data: The dataset which needs to be analyzed
    :param lowerIndex: The lower index of the subset that is to be analyzed
    :param upperIndex: The upper index of the subset that is to be analyzed
    :return: A value between 0 and 1. The higher this value is, the worse the dataset is.
    """
    gaps = np.diff(data[0][lowerIndex:upperIndex])
    ind,values = getMostCommonStep(data)
    # adding 0.1, just to be sure not to get very small flukes in the observation time
    totalGap = np.sum(gaps[gaps>values[ind]+0.1])

    return totalGap/(data[0][upperIndex]-data[0][lowerIndex])



@timeit
def find_nearest(array: np.ndarray, value: float) -> int:
    """
    Finds the index of the nearest value to a value in an array.
    :param array Array to be checked in:
    :param value value that needs to be found in array:
    :return index of nearest value:
    """
    idx = (np.abs(array-value)).argmin()
    return int(idx)

@timeit
def writeResults(file: str, data: Dict[Tuple[float,float],List[Tuple[float,float]]], mode: str = 'w'):
    """
    This function writes the results of the analysis. The file will have a structure like this:
    Lowerrange Upperrange
    0 50
        frequency snr
        0.00    25
    :param file File where the results have to be written.
    :param data The dataset that is to be written. Needs to be a dict, where the key is a tuple containing min/max
    time points of the chunk, and the value a list of tuples, containing the frequencies and their corresponding snr
    :param mode write mode. Default is 'w':
    """
    with open(file,mode) as f:
        f.write("Lowerrange Upperrange\n")
        for key,value in data.items():
            f.write(str(key[0]) + " " + str(key[1])+"\n")
            f.write("   frequency snr amp phase"+"\n")

            for i in value:
                text = "    "
                for j in i:
                    text +=str(j)+" "
                text +="\n"
                f.write(text)

@timeit
def createPath(path):
    """
    This function creates a path if it doesn't exist
    :param path path to be created:
    """
    if not os.path.exists(path):
        os.mkdir(path)

@timeit
def saveAmpSpectrumAndImage(ampSpectrum: np.ndarray, path: str, name: str):
    """
    This function saves the amplitude spectrum and according plots to the results path.
    :param name name of file and image:
    """
    createPath(path)

    with cd(path):
        np.savetxt(name+".txt",ampSpectrum.T)
        plotData = {"Amplitude Spectrum":(ampSpectrum, geom_line, 'solid')}
        p = plotCustom(name,plotData,xLabel="Frequency(c/d)",yLabel="Amplitude")
        p.save(name+".pdf")
