from files import *
from timeseries import *
from plotter import *
import warnings
from stem.util import term

def run(file,snrCriterion,windowSize,**kwargs):
    data = readData(file)
    data = normalizeData(data)
    splitLists = getSplits(data,kwargs['timeRange'],kwargs['overlap'])
    result = {}
    for data in splitLists:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            frequencyList = recursiveFrequencyFinder(data,kwargs['frequencyRange'],snrCriterion,windowSize)
        print(term.format("Range from "+str(data[0][0])+" to "+str(max(data[0])), term.Color.GREEN))
        print("Length of frequencyList: "+str(len(frequencyList)))
        print("Frequencies: "+str(frequencyList))
        result[(data[0][0],max(data[0]))] = frequencyList

    writeResults("results.txt",result)

