#!/usr/bin/env python
import argparse
from smurfs._smurfs.smurfs import Smurfs
from smurfs._smurfs.multi_smurfs import MultiSmurfs
from smurfs.__version__ import __version__
from smurfs.support.mprint import *
import os
import pickle
import subprocess
import sys
import warnings


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()

    parser.add_argument("target", help="Target for the frequency analysis. Can be either a target, or "
                                       "a star name. If it is a target, it needs to be an ASCII target. "
                                       "The first two rows are expected to be time "
                                       "and flux, the third row is optional and can be used as the flux "
                                       "error.", type=str)
    parser.add_argument("snr", help="The desired lower bound for the signal to noise ratio for the analysis",
                        type=float)
    parser.add_argument("windowSize", help="The window size used to get the SNR for a given frequency", type=float)
    parser.add_argument("-fr", "--frequencyRange",
                        help="Optional parameter that describes the desired frequency range. "
                             "The application will only check within this parameters if given. "
                             "Per default this parameter is set from 0 to Nyquist frequency."
                             "Please enter it in a form of a tuple (lower,higher).",
                        type=str, default="None,None")

    parser.add_argument("-ssa", "--skipSimilarFrequencies", help="If this parameter is set, the frequencies surrounding"
                                                                 "one frequency are in a very similar range, that area "
                                                                 "will be ignored", action='store_true')

    parser.add_argument("-sc", "--skipCutoff",
                        help="Skips the cutoff check, so similar frequencies don't chancel the run. Be aware that this "
                             "might lead to unknown behaviour",
                        action='store_true')

    parser.add_argument("-ef", "--extendFrequencies",
                        help="Extends the frequency analysis by n frequencies, meaning, the analysis will only stop"
                             "after n insignificant frequencies are found.", type=int, default=0)

    parser.add_argument("-imf", "--improveFitMode",
                        help="Three different fit improvement modes are available:\n1)'all' "
                             "-> improve fit after every frequency\n2)'end' -> improve "
                             "fit after last significant frequency was found.\n3) 'none' -> "
                             "Disables improve fit.", type=str, choices=['all', 'end', 'none'],
                        default='all')

    parser.add_argument("-fm", "--fitMethod", help="Using this flag you can either choose 'scipy' "
                                                   "(scipy.optimize.curve_fit) or 'lmfit' (lmfti Model fit). "
                                                   "'lmfit' is activated by default",
                        type=str, choices=["scipy", "lmfit"], default="lmfit")

    parser.add_argument("-ft", "--fluxType", help="If you input SC Tess observations (TIC IDs), this flag "
                                                  "allows you to choose between PDCSAP and SAP flux or PSF for long "
                                                  "cadence data. Default "
                                                  "is PDCSAP",
                        type=str, choices=["PDCSAP", "SAP", "PSF"], default="PDCSAP")

    parser.add_argument("-so", "--storeObject", help="If this flag is set, the SMURFS object is stored in the "
                                                     "results. You can later use this object to load the "
                                                     "_result into a python file using 'Smurfs.from_path'."
                        , action='store_true')

    parser.add_argument("-sp", "--savePath", help="Allows you to set the save path of the analysis. By "
                                                  "default it will save it in the same folder, where "
                                                  "the module was called.", type=str, default=".")

    parser.add_argument("-i", "--interactive", help="Using this flag will automatically start an iPython shell. "
                                                    "This allows for direct interaction with the result using the "
                                                    "'star' object."
                        , action='store_true')

    parser.add_argument("-m", "--mission", help="Three different missions are available: Kepler,TESS,K2. You can choose"
                                                " the mission by setting this value. By default, only TESS missions are"
                                                " considered"
                        , type=str, choices=["Kepler", "TESS", "K2"], default="TESS")

    parser.add_argument("-cl", "--sigmaClip", help="Sets the sigma for the sigma clipping. Default is 4.", type=float,
                        default=4)
    parser.add_argument("-it", "--iters", help="Sets the iterations for the sigma clipping. Default is 1.", type=int,
                        default=1)

    parser.add_argument("-pca", "--do_pca",
                        help="Activates the PCA analysis (aperture × TPF + background subtraction + "
                             "cotrending basis vectors).Only "
                             "applicable to extraction from TESS FFIs", action='store_true')

    parser.add_argument("-psf", "--do_psf", help="Activates the PSF analysis. This adds point spread function "
                                                 "modelling to the extraction of light curves from FFIs. Only "
                                                 "applicable to extraction from TESS FFIs", action='store_true')

    parser.add_argument("-ac", "--apply_corrections",
                        help="If this flag is set, correctsion (sigma clipping, conversion"
                             " to magnitude) are applied to files", action='store_true')

    """
    #todo replace this
    parser.add_argument("-om", "--outputMode", help="Optional parameter that defines what will be exported as dataset. "
                                                    "There are two possibilities: Normal and Full. Normal mode means, that"
                                                    "only the first and last amplitudespectra will be plotted & exported, "
                                                    "full means all amplitudespectra will be plotted & exported. Default is "
                                                    "Normal.",
    
                        type=str, choices=["Normal", "Full"], default="Normal")
                        
    parser.add_argument("-igr", "--ignoreCutoffRatio", help="Optional parameter. If this is set to True, it will ignore"
                                                            "the gap ratio cutoff criterion", action='store_true')  
                                                            
    parser.add_argument("-trs", "--timeBaseSplit",
                        help="Optional parameter that describes the split within the time range."
                             "This can be used to get multiple amplitude spectra for the "
                             "lightcurve, split up within the time Range. A parameter could be "
                             "for example 50, where the parameter would split the lightcurve in"
                             "50 day chunks (last segment will be smaller/equal). Defaults"
                             "to -1, which means no splitting will occur",
                        type=int, default=-1)
    parser.add_argument("-o", "--overlap",
                        help="Optional parameter that describes the overlap of two split ranges. Will only"
                             "work, if -trs is set to a reasonable parameter. For example, if the trs is "
                             "set to 50 and the overlap to 2, the chunks would contain the ranges (0,50),"
                             "(48,98),(96,146) ... Defaults to 0, which means no overlap will take place",
                        type=int, default=0)                                                                                  
    """
    parser.add_argument("--version", help="Shows version of SMURFS", action='version',
                        version='SMURFS {version}'.format(version=__version__))

    args = parser.parse_args(args)

    if "," in args.target:
        targets = args.target.split(",")
    else:
        targets = [args.target]

    f_min = None if args.frequencyRange.split(",")[0] == 'None' else float(args.frequencyRange.split(",")[0])
    f_max = None if args.frequencyRange.split(",")[1] == 'None' else float(args.frequencyRange.split(",")[1])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if len(targets) == 1:
            target = targets[0]

            if len(target.split(".")) == 2 and os.path.basename(target).split(".")[1] in ['txt', 'dat']:
                s = Smurfs(file=target, flux_type=args.fluxType, mission=args.mission, sigma_clip=args.sigmaClip,
                           iters=args.iters, do_pca=args.do_pca, do_psf=args.do_psf,
                           apply_file_correction=args.apply_corrections)
            else:
                s = Smurfs(target_name=target, flux_type=args.fluxType, mission=args.mission, sigma_clip=args.sigmaClip,
                           iters=args.iters, do_pca=args.do_pca, do_psf=args.do_psf)

            improve_fit = args.improveFitMode == 'all'

            s.run(snr=args.snr, window_size=args.windowSize, f_min=f_min, f_max=f_max,
                  skip_similar=args.skipSimilarFrequencies, similar_chancel=not args.skipCutoff
                  , extend_frequencies=args.extendFrequencies, improve_fit=improve_fit
                  , mode=args.fitMethod)

            if args.improveFitMode == 'end':
                mprint("Improving fit ...", state)
                s.improve_result()

            s.save(args.savePath, args.storeObject)

            # start interactive shell, by loading smurfs object directly into the shell
            if args.interactive:
                mprint("Starting interactive shell. Use the 'star' object to interact with the result!", state)
                pickle.dump(s, open("i_obj.smurfs", "wb"))
                cmd = ["ipython", "-i", "-c",
                       "from smurfs import Smurfs;import pickle;star : Smurfs = pickle.load(open('i_obj.smurfs', 'rb'));import os;os.remove('i_obj.smurfs');import matplotlib.pyplot as pl;pl.ion()"]
                subprocess.call(cmd)
                mprint("Done", info)
        else:
            if len(targets[0].split(".")) == 2 and os.path.basename(targets[0]).split(".")[1] in ['txt', 'dat']:
                s = MultiSmurfs(file_list=targets)
            else:
                s = MultiSmurfs(target_list=targets, flux_types=args.fluxType)

            s.run(snr=args.snr, window_size=args.windowSize, f_min=f_min, f_max=f_max,
                  skip_similar=args.skipSimilarFrequencies, similar_chancel=not args.skipCutoff
                  , extend_frequencies=args.extendFrequencies, improve_fit=args.disableImproveFrequencies
                  , mode=args.fitMethod)
            s.save(args.savePath, args.storeObject)


if __name__ == "__main__":
    main()
