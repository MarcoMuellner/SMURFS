import numpy as np
from smurfs.support import *
from typing import List,Dict,Tuple
from collections import OrderedDict
from uncertainties import unumpy
from astroquery.mast import Observations
from astropy.io import fits
import os
@timeit
def normalizeData(data: np.ndarray) -> np.ndarray:
    """
    This function reduces the dataset to make computations easier. It subtracts the 0 point in the temporal axis and
    removes the mean of the dataset.
    :param data: The dataset, probably read through readData
    :return: A normalized dataset
    """
    data[0] -= data[0][0]

    data = reduce_y(data)
    return data

def reduce_y(data: np.ndarray) -> np.ndarray:
    x = data[0]
    y = data[1]

    for i in ['nan','-nan']:
        if i in y.astype(str):
            n = len(y[y.astype(str)==i])
            print(term.format(f"You have {n} {i} in your data. These points will be removed.",term.Color.YELLOW))

        x = x[y.astype(str) != i]
        y = y[y.astype(str) != i]

    for i in [np.inf,-np.inf,np.nan]:
        if i in y:
            n = len(y[y==i])
            print(term.format(f"You have {n} {i} in your data. These points will be removed.",term.Color.YELLOW))

        x = x[y != i]
        y = y[y != i]

    y -= np.mean(y)
    return np.array((x, y))


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

    arg = np.argsort(data[0])
    data = np.array((data[0][arg],data[1][arg]))

    if data[0][0] != 0:
        data = normalizeData(data)

    if timeRange == -1:
        timeRange = max(data[0])
    dataPoints = []
    i = 0

    if not i*(timeRange-overlap)+timeRange <= max(data[0]):
        timeRange = max(data[0])

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
    ind = int(np.argmax(counts))
    if counts[ind]*100/np.sum(counts) < 10:
        counts[ind] = np.median(np.diff(data[0]))
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
    totalGap = np.sum(gaps[gaps>(1.2*values[ind])])

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
def writeResults(file: str, data: Dict[Tuple[float,float],List[Tuple[float,float]]],nyquistFrequency : float, mode: str = 'w'):
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

    for key,value in data.items():
        savePath = "{0:0=3d}".format(int(key[0]))
        savePath += "_{0:0=3d}/".format(int(key[1]))
        header = "f(c/d) f_err(c/d) snr amp amp_err phase phase_err residual_noise"
        arr = []
        for i in value:
            val_list = []
            for j in i:
                try:
                    val_list.append(j.nominal_value)
                    val_list.append(j.std_dev)
                except AttributeError:
                    val_list.append(j)
            arr.append(val_list)

        np.savetxt(savePath+file,np.array(arr),header=header,comments=f"Nyquist frequency(c/d):{nyquistFrequency}\n")

@timeit
def createPath(path):
    """
    This function creates a path if it doesn't exist
    :param path path to be created:
    """
    if not os.path.exists(path):
        os.makedirs(path)

def save_frequency_spacing(data : np.ndarray, path: str, name : str):
    createPath(path)
    with cd(path):
        try:
            val =  unumpy.nominal_values(data)
        except: # for uncertainties values
            val = data

        np.savetxt(f"{name}.txt", val.T)

        fig = pl.figure()
        pl.hist(val, bins='auto', color='k', rwidth=0.9)
        pl.xlabel(r"Frequency spacing ($d^{-1}$)")
        pl.ylabel("Counts")
        pl.title("Frequency spacing overview")
        fig.savefig(f"{name}.pdf")
        pl.close()



@timeit
def saveAmpSpectrumAndImage(ampSpectrum: np.ndarray, path: str, title : str,file_name: str):
    """
    This function saves the amplitude spectrum and according plots to the results path.
    :param name name of file and image:
    """
    createPath(path)

    with cd(path):
        np.savetxt(file_name+".txt",ampSpectrum.T)
        plotData = {title:(ampSpectrum, '-')}
        p = plotCustom(title,plotData,xLabel="Frequency(c/d)",yLabel="Amplitude")
        p.savefig(file_name+".pdf")
        pl.close()


def download_tic(tic_id : str):
    obsTable = Observations.query_criteria(dataproduct_type=["TIMESERIES"], obs_collection="TESS",target_name=tic_id)
    if len(tic_id) == 0:
        raise ValueError(f"Cannot find TESS data for {tic_id}")
    dataProductsByID = Observations.get_product_list(obsTable)
    Observations.download_products(dataProductsByID)
    fits_files = []
    for path,subfolder,files in os.walk("mastDownload"):
        tic_folders = []
        for folder in subfolder:
            if tic_id in folder:
                tic_folders.append(folder)

        if tic_folders == []:
            continue

        for folder in tic_folders:
            for _,_,files in os.walk(f"{path}/{folder}"):
                for i in files:
                    if i.endswith("lc.fits"):
                        fits_files.append(f"{path}/{folder}/{i}")

    if fits_files == []:
        raise ValueError(f"Couldn find proper TESS Data for {tic_id}")

    for file in fits_files:
        hdulist = fits.open(file)
        try:
            data_new = np.array((hdulist[1].data["TIME"], hdulist[1].data["PDCSAP_FLUX"]))
            data_new = reduce_y(data_new)
            data = np.hstack((data,data_new))
        except:
            data = np.array((hdulist[1].data["TIME"],hdulist[1].data["PDCSAP_FLUX"]))
            data = reduce_y(data)

    y = data[1] + 2*abs(min(data[1]))
    y = -2.5*np.log(y*2.5*10**(-18)/1000)
    y -= np.mean(y)
    data = np.array((data[0],y))

    return data
