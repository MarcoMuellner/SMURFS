from files import *
from timeseries import *
from plotter import *
import warnings
from stem.util import term

def run(file,snrCriterion,windowSize,frequencyRange,timeRange,overlap,mode):
    data = readData(file)
    data = normalizeData(data)
    splitLists = getSplits(data,timeRange,overlap)
    for data in splitLists:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            frequencyList = recursiveFrequencyFinder(data,frequencyRange,snrCriterion,windowSize)
        print(term.format("Range from "+str(data[0][0])+" to "+str(max(data[0])), term.Color.GREEN))
        print("Length of frequencyList: "+str(len(frequencyList)))
        print("Frequencies: "+str(frequencyList))
