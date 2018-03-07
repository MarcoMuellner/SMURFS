import numpy as np
import os
from support import cd,plotCustom
from plotnine import *

def normalizeData(data):
    data[0] -= data[0][0]
    data[1] -= np.mean(data[1])
    return data


def readData(file):
    if not os.path.exists(file):
        raise IOError("File " + file + " doesn't exist!")

    return np.loadtxt(file).T

def getSplits(data,timeRange=-1,overlap=0):
    if timeRange == -1:
        timeRange = max(data[0])
    dataPoints = []
    i = 0
    while(i*(timeRange-overlap)+timeRange <= max(data[0])):
        lowerIndex = find_nearest(data[0],i*(timeRange-overlap))
        upperIndex = find_nearest(data[0],i*(timeRange-overlap)+timeRange)
        array = np.array((data[0][lowerIndex:upperIndex],data[1][lowerIndex:upperIndex]))
        dataPoints.append(array)
        i +=1
    return dataPoints

def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return int(idx)

def writeResults(file,data,mode='w'):
    with open(file,mode) as f:
        f.write("Lowerrange Upperrange\n")
        for key,value in data.items():
            f.write(str(key[0]) + " " + str(key[1])+"\n")
            f.write("   frequency snr"+"\n")
            for i in value:
                f.write("   "+str(i[0])+" "+str(i[1])+"\n")

def createPath(path):
    if not os.path.exists(path):
        os.mkdir(path)

def saveAmpSpectrumAndImage(ampSpectrum,path,name):
    if not os.path.exists(path):
        os.mkdir(path)

    with cd(path):
        np.savetxt(name+"spectrum.txt",ampSpectrum.T)
        plotData = {"Amplitude Spectrum":(ampSpectrum.T, geom_line, 'solid')}
        p = plotCustom(name,plotData,xLabel="Frequency",yLabel="Amplitude")
        p.save(name+".png")