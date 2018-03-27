import argparse
from smurfs.analysis import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("fileName",help="The filename of the lightcurve. Has to be a text file. Please provide "
                                        "absolute path",type=str)
    parser.add_argument("snr",help="The desired lower bound for the signal to noise ratio for the analysis",type=float)
    parser.add_argument("windowSize",help="The window size used to get the SNR for a given frequency",type=float)
    parser.add_argument("-fr","--frequencyRange",help="Optional parameter that describes the desired frequency range. "
                                                      "The application will only check within this parameters if given. "
                                                      "Per default this parameter is set from 0 to Nyquist frequency."
                                                      "Please enter it in a form of a tuple (lower,higher).",
                        type=str,default="0,100")
    parser.add_argument("-trs","--timeBaseSplit",help="Optional parameter that describes the split within the time range."
                                                       "This can be used to get multiple amplitude spectra for the "
                                                       "lightcurve, split up within the time Range. A parameter could be "
                                                       "for example 50, where the parameter would split the lightcurve in"
                                                       "50 day chunks (last segment will be smaller/equal). Defaults"
                                                       "to -1, which means no splitting will occur",
                        type=int,default=-1)
    parser.add_argument("-o","--overlap",help="Optional parameter that describes the overlap of two split ranges. Will only"
                                              "work, if -trs is set to a reasonable parameter. For example, if the trs is "
                                              "set to 50 and the overlap to 2, the chunks would contain the ranges (0,50),"
                                              "(48,98),(96,146) ... Defaults to 0, which means no overlap will take place",
                        type=int,default=0)
    parser.add_argument("-om","--outputMode",help="Optional parameter that defines what will be exported as dataset. "
                                                  "There are two possibilities: Normal and Full. Normal mode means, that"
                                                  "only the first and last amplitudespectra will be plotted & exported, "
                                                  "full means all amplitudespectra will be plotted & exported. Default is "
                                                  "Normal.",
                        type=str,choices=["Normal","Full"],default="Normal")


    args = parser.parse_args()

    fData = args.frequencyRange.split(",")
    frequencyRange = (float(fData[0]),float(fData[1]))

    run(args.fileName,args.snr,windowSize=args.windowSize
                                ,frequencyRange=frequencyRange
                                ,timeRange=args.timeBaseSplit
                                ,overlap=args.overlap
                                ,outputMode=args.outputMode)









