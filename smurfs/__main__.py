import argparse
from smurfs.analysis import *
from smurfs._version import __version__
from smurfs.support.config import UncertaintyMode,conf

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
    parser.add_argument("-fm","--frequencyMarker",help="Optional parameter, that can be passed if frequencies should be "
                                                       "marked in the dynamic fourier spektrum. Frequencies will be plotted "
                                                       "on top of the plot. Please use a relative path to the call path "
                                                       "you are currently in",
                        type=str,default="")
    parser.add_argument("--version",help="Shows version of SMURFS",action='version',
                        version='SMURFS {version}'.format(version=__version__))

    parser.add_argument("-igr","--ignoreCutoffRatio",help="Optional parameter. If this is set to True, it will ignore"
                                                          "the gap ratio cutoff criterion",action='store_true')

    parser.add_argument("-ssa","--skipSimilarFrequencies",help="If this parameter is set, the frequencies surrounding"
                                                               "one frequency are in a very similar range, that area "
                                                               "will be ignored",action='store_true')

    parser.add_argument("-um","--uncertaintyMode", help="Optional parameter. Set this parameter to choose the "
                                                         "error determination. Either Montgomery & O'Donoghue (1999),"
                                                         "least square errors (fits) or none", type=str
                        , choices=UncertaintyMode.content(), default=UncertaintyMode.fit.value)

    args = parser.parse_args()

    if "," in args.fileName:
        files = args.fileName.split(",")
    else:
        files = [args.fileName]

    for file in files:
        conf().uncertaintiesMode = args.uncertaintyMode
        conf().skipSimilarFrequencies = args.skipSimilarFrequencies

        fData = args.frequencyRange.split(",")
        frequencyRange = (float(fData[0]), float(fData[1]))

        run(file,args.snr,windowSize=args.windowSize
                                    ,frequencyRange=frequencyRange
                                    ,timeRange=args.timeBaseSplit
                                    ,overlap=args.overlap
                                    ,outputMode=args.outputMode
                                    ,frequencyMarker=args.frequencyMarker
                                    ,ignoreCutoffRatio=args.ignoreCutoffRatio)









