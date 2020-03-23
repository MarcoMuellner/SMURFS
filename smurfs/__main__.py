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


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("target", help="This parameter represents the target analyzed by SMURFS. This parameter is "
                                       "rather vague, to give you the maximum amount of flexibility. Either you can "
                                       "provide any name of a star (resolvable through Simbad) that has been observed "
                                       "by TESS/Kepler/K2. You can also provide a filename through this parameter.\n\n"
                                       "If you choose to do the the first, the code prioritizes TESS over all "
                                       "other missions (if you don't provide the mission parameter), and SC over LC "
                                       "observations. It then checks MAST if there are SC observations "
                                       "from TESS for this star. If there are, it uses "
                                       "*lightkurve.search_lightcurvefile* to download those."
                                       " If there are none, it checks if there are "
                                       "LC observations from TESS and uses Eleanor to extract the light curves "
                                       "from the FFIs. If there are None, it searches all other missions "
                                       "for light kurves of this object.If you choose another "
                                       " mission, it will call *lightkurve.search_lightcurvefile* for this specific "
                                       "mission.\n\nIf you choose to provide "
                                       "a file through this parameter, make sure that you follow these conventions:\n\n"
                                       "- The file must be an ASCII file\n\n"
                                       "- The first column must contain the time stamps\n\n"
                                       "- The second column must contain the flux\n\n"
                                       "- If a third column exists, SMURFS will assume that these are the uncertainties in the flux."
                                       "\n\n\nSMURFS will take the file as is and won't apply "
                                       "any corrections to it, if you don't use the *apply_corrections* flag. "
                                       "It then assumes that the flux values are in magnitude and varying "
                                       "around 0, that the time stamps are in days and that the "
                                       "data set is properly reduced.", type=str)
    parser.add_argument("snr",
                        help="This parameter represents the lower bound signal to noise ratio any frequency must have. SMURFS "
                             "computes the SNR by taking the amplitude of an individual frequency (as defined by the amplitude in the frequency "
                             "spectrum). Next, it applies half of the window size to either side of the frequency, starting by the next adjacent "
                             "minima, and takes the mean of this window as the noise surrounding the frequency. The ratio of these two values is "
                             "the resulting SNR for an individual frequency. By default, SMURFS stops its run when the first frequency less than "
                             "this value has been found",
                        type=float)
    parser.add_argument("windowSize", help="The window size used to get the SNR for a given frequency. SMURFS "
                                           "defines the window as half of the given value on each side of the peak "
                                           "in the periodogram, starting from the first minima next to the peak.",
                        type=float)
    parser.add_argument("-fr", "--frequencyRange",
                        help="Setting this parameter, allows you to restrict the analysis "
                             "of a time series to a given range in the frequency spectrum. This might be useful, if yo have a lot of high "
                             "amplitude noise in another part of the spectrum, than the one you might be interested in. Provide the parameter "
                             "in the form *0,100*.",
                        type=str, default="None,None")

    parser.add_argument("-ssa", "--skipSimilarFrequencies",
                        help="Ignores regions where SMURFS finds multiple frequencies within a small range. "
                             "This can happen due to insufficient fits or signals that are hard to fit.",
                        action='store_true')

    parser.add_argument("-sc", "--skipCutoff",
                        help="By default, SMURFS stops the extraction of frequencies if it finds 10 frequencies in a row"
                             "that have a standard deviation of <0.05, as it assumes it can't work itself out of "
                             "this region. You can override this behaviour by setting this flag. Be aware, that "
                             "this might lead to unknown behaviour. Usually, instead of setting this flag, it is "
                             "better to set the -ssa flag",
                        action='store_true')

    parser.add_argument("-ef", "--extendFrequencies",
                        help="Extends the analysis by n frequencies. By default, SMURFS stops when it finds the first "
                             "insignificant frequency. Setting this parameter requires SMURFS to find n insignificant "
                             "frequencies in a row.", type=int, default=0)
    parser.add_argument("-fd","--frequencyDetection",help="If this value is set, a found frequency is compared to the "
                                                          "original periodogramm. If the ratio between the "
                                                          "amplitude of the found frequency and the maximum in "
                                                          "the range of the found frequency on the original "
                                                          "periodogram is lower than the set value, it will "
                                                          "ignore this frequency range going forward.",type=float,
                        default=None)

    parser.add_argument("-imf", "--improveFitMode",
                        help="This parameter defines the way SMURFS uses a Period04 like improvement of frequencies."
                             " You can set the following modes:\n\n"
                             "- *all*: Tries to refit all found frequencies after every frequeny that is found. This is the usual behaviour of Period04 and the default setting.\n\n"
                             "- *end*: Improves the frequencies after SMURFS would stop its run\n\n"
                             "- *none*: Disables the improve frequencies setting. This can be useful if you find a lot of frequencies and the run would take an unnecessary amount of time\n\n"
                        , type=str,
                        choices=['all', 'end', 'none'],
                        default='all')

    parser.add_argument("-fm", "--fitMethod",
                        help="SMURFS implements two different fitting libraries: Either it uses *scipy* "
                             "(scipy.optimize.curve_fit) or *lmfit* (lmfit Model fit). Choosing one over the other "
                             "might lead to different results, so if you have find an unexpected result, try "
                             "to switch the fitting mode.",
                        type=str, choices=["scipy", "lmfit"], default="lmfit")

    parser.add_argument("-ft", "--fluxType",
                        help='The TESS mission gives its end users different data products to choose, if you download '
                             'them directly from MAST. You can pass the type of data product you like using this '
                             'parameter. For the SC data, where the light curve is preprocessed by SPOC, you can choose'
                             'two different products: \n\n'
                             '- *SAP flux*: SAP is the simple aperture photometry flux (resulting light curve is the flux after summing the calibrated pixels within the TESS optimal aperture)\n\n'
                             '- *PDCSAP flux*: PDCSAP is the Pre-search Data conditioned Simple aperture photometry, which is corrected using co-trending basis vectors.'
                             '\n\n\nBy default we use the PDCSAP flux, but you can also '
                             'choose another one if you like.\n\n\nIf your target is only observed in LC mode, SMURFS '
                             'also provides these two modes (these have a slightly different meaning, their '
                             'result is however equivalent to the SC SAP and PDSCAP fluxes, see the Eleanor '
                             'documentation). However, in LC mode you have also the PSF flux type, which models a '
                             'point spread function for a given star. The validation page generated when SMURFS '
                             'extracts a target from a FFI always shows the SAP and the chosen flux to compare. You '
                             'might want to try different settings, depending on your use case',
                        type=str, choices=["PDCSAP", "SAP", "PSF"], default="PDCSAP")
    parser.add_argument("-pca", "--do_pca",
                        help="Activates the PCA analysis (aperture × TPF + background subtraction + "
                             "cotrending basis vectors). This doesn't change the data you are trying to analyze, "
                             "but shows the PDSCAP flux in the validation page. Only applicable "
                             "when using LC data.", action='store_true')
    parser.add_argument("-psf", "--do_psf", help="Activates the PSF analysis. This adds point spread function "
                                                 "modelling to the extraction of light curves from FFIs.  This doesn't "
                                                 "change the data you are trying to analyze, "
                                                 "but shows the PSF flux in the validation page. Only applicable "
                                                 "when using LC data.", action='store_true')

    parser.add_argument("-so", "--storeObject", help="If this flag is set, the SMURFS object is stored in the "
                                                     "results. You can later use this object to load the "
                                                     "_result into a python file using 'Smurfs.from_path'. Allows "
                                                     "you to easily access all convenience functions from SMURFS."
                        , action='store_true')

    parser.add_argument("-sp", "--savePath", help="Allows you to set the save path of the analysis. By "
                                                  "default it will save it in the same folder, where "
                                                  "the module was called.", type=str, default=".")

    parser.add_argument("-i", "--interactive", help="Using this flag will automatically start an iPython shell. "
                                                    "This allows for direct interaction with the result using the "
                                                    "'star' object. You can then access all convenience functions "
                                                    "directly (like plotting, the FrequencyFinder object, etc)."
                        , action='store_true')

    parser.add_argument("-m", "--mission", help="Three different missions are available: Kepler,TESS,K2. You can choose"
                                                " the mission by setting this value. By default, only TESS missions are"
                                                " considered"
                        , type=str, choices=["Kepler", "TESS", "K2"], default="TESS")

    parser.add_argument("-cl", "--sigmaClip", help="Sets the sigma for the sigma clipping. Default is 4.", type=float,
                        default=4)
    parser.add_argument("-it", "--iters", help="Sets the iterations for the sigma clipping. Default is 1.", type=int,
                        default=1)

    parser.add_argument("-ac", "--apply_corrections",
                        help="If this flag is set, correction (sigma clipping, conversion"
                             " to magnitude) are applied to files. Make sure that your flux is in "
                             "electron counts if you use this flag.", action='store_true')

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
    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = get_parser()
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

            if os.path.exists(target) and os.path.isfile(target):
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
                  , mode=args.fitMethod,frequency_detection=args.frequencyDetection)

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
