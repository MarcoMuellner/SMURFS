import numpy as np
import os

def normalizeData(data):
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])
    return data


def readData(file):
    if not os.path.exists(file):
        raise IOError("File " + file + " doesn't exist!")

    return np.loadtxt(file).T

def getSplits(data,timeRange,overlap=0):
    if timeRange == -1:
        timeRange = max(data[0])
    dataPoints = []
    i = 0
    while(i*(timeRange-overlap)+timeRange < max(data[0])):
        lowerIndex = find_nearest(data[0],i*(timeRange-overlap))
        upperIndex = find_nearest(data[0],i*(timeRange-overlap)+timeRange)
        array = np.array((data[0][lowerIndex:upperIndex],data[1][lowerIndex:upperIndex]))
        dataPoints.append(array)
        i +=1
    return dataPoints

def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return int(idx)