from smurfs.files import *
from smurfs.timeseries import *
from smurfs.support import *
import datetime

@timeit
def run(file: str, snrCriterion: float, windowSize: float, **kwargs):
    """
    This function perfomrs a full analysis of a given star. Initially it will split up the dataset according to
    the parameters and than run the recursiveFrequencyFinder, which will return the frequencylist for the given split
    of the original dataset. At the end it will write a results File, containing all splits with their corresponding
    significant (read snr > snrcriterion) frequencies and snrs.
    A results folder will also be created, wherein the first and last amplitude spectrum are stored as well as a plot of
    these.
    :param file: The path to the file where the lightCurve is stored. The lightcurve should contain the time axis in
    its first column and the luminosity in its second column. The code doesn't check against any kind of units, it is
    therefore the responsibility of the user to properly analyse the data afterhand.
    :param snrCriterion: This parameter defines the cutoff criterion for the analysis. It will therefore gather
    frequencies up to the point where its respective SNR is smaller than this snrcriterion.
    :param windowSize: The window size defines the box around the peak from where the noise is calculated. Keep in mind,
    that the window is neither necessarily symmetric nor is the left side and right side of the box starting at the
    peak. To determine the box, it will search for a minimum adjacent to the peak and start the box from this minimum
    on.
    :param kwargs: kwargs defines some other parameters that can be used to steer the code properly. These include:
        - timeRange: The timeRange parameter defines the "box" where the analysis takes place. For example, if the
        dataSet is 450 days long and the timeRange parameter is set to 50, it will split this dataSet in equal size
        chunks, and an independent analysis is performed for each chunk. These can also overlap,
        using the overlap parameter.
        - overlap: The overlap paramater defines the overlap between two chunks, which size is determined by the
        timeRange parameter. Assume the timeRange parameter is set to 50, and the overlap parameter is set to 2. The
        chunks will than represent the dataset from 0->50,48->98,96->146, ...
        - frequencyRange: The frequencyRange parameter defines the frequency range where the dataset is constrained to.
        This will vastly improve speed, but could cut off significant frequencies
        - frequencyMarker: Adds frequency marker to the dynamic fourier plot. If None, no are added.
    """
    print(term.format(f"Running {file}",term.Color.GREEN))
    print(term.format(f"-------------------------------------------", term.Color.GREEN))
    start_time = datetime.datetime.now()
    fileData = readData(file)
    fileData = normalizeData(fileData)
    splitLists = getSplits(fileData,kwargs['timeRange'],kwargs['overlap'],kwargs['ignoreCutoffRatio'])

    try:
        frequencyMarker = readFrequencyMarker(kwargs['frequencyMarker'])
    except FileNotFoundError:
        if not kwargs['frequencyMarker'] == "":
            print(term.format("File {0} was not found. No marker will be added to "
                              "dynamic fourier plot!".format(kwargs['frequencyMarker']),term.Color.RED))
        frequencyMarker = None
    except ValueError as e:
        print(term.format("Error in frequency Marker file. Error: {0}".format(e),term.Color.RED))
        frequencyMarker = None

    result = {}
    path = f"results/{file.split('/')[-1].split('.')[0]}_snr_{int(snrCriterion)}_w_{int(windowSize)}"
    if kwargs['timeRange'] != -1:
        path +=f"_trs_{int(kwargs['timeRange'])}"
    if kwargs['overlap'] != 0:
        path +=f"_o_{int(kwargs['overlap'])}"
    if kwargs['frequencyRange'] != (0,100):
        path +=f"_fr_{int(kwargs['frequencyRange'][0])}_{int(kwargs['frequencyRange'][1])}"

    path+="/"

    createPath(path)
    fList = []
    tList = []
    iList = []
    total_f = 0
    with cd(path):
        for data in splitLists:
            print(term.format("Time base from " + str(int(data[0][0])) + " to " + str(int(max(data[0])))+ " days", term.Color.GREEN) )
            print(term.format("Calculation from "+str(kwargs['frequencyRange'][0])+"c/d to "+str(kwargs['frequencyRange'][1])+"c/d",term.Color.GREEN))

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    frequencyList,f,t,i = recursiveFrequencyFinder(data,snrCriterion,windowSize
                                                         ,frequencyRange=kwargs['frequencyRange'],mode=kwargs['outputMode'])
                except (ValueError,IndexError):
                    print(term.format("Time base from "+ str(int(data[0][0])) + " to " + str(int(max(data[0])))+ "failed "
                             "to perform Lomb-Scargle. Cannot determine Spectrum. Skipping this sector",term.Color.RED))
                    continue

                fList.append(f)
                tList.append(t)
                iList.append(i)

                print(term.format(f"Residual noise {abs(frequencyList[-1][4])}", term.Color.GREEN))

                total_f += len(frequencyList)
                result[(data[0][0], max(data[0]),frequencyList[-1][4])] = frequencyList
                if defines.dieGracefully:
                    break

        f,t,i = combineDatasets(fList,tList,iList)
        if kwargs['timeRange'] == -1:
            tMax = max(t)
        else:
            tMax = max(t) - kwargs['overlap']
        plotMesh(f,t,i,frequencyList = frequencyMarker,minimumIntensity = defines.minimumIntensity,tMax = tMax)


        waitForProcessesFinished()
        writeResults("results.txt",result,nyquistFrequency(fileData))

        gap_ratio = getGapRatio(fileData,0,len(fileData[0])-1)

        delta = datetime.datetime.now() - start_time
        minutes = delta.seconds//60
        rest_seconds = delta.seconds%60
        print(term.format(f"Total runtime: {minutes} minutes and {rest_seconds} seconds",term.Color.GREEN))
        print(term.format(f"Duty cycle: {'%.2f'%((1-gap_ratio)*100)}%", term.Color.GREEN))
        print(term.format(f"Total found frequencies: {total_f}", term.Color.GREEN))

