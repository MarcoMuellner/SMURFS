# SMURFS [![Build Status](https://travis-ci.org/muma7490/SMURFS.svg?branch=master)](https://travis-ci.org/muma7490/SMURFS)
![SMURFS Image](https://i.imgur.com/wWe1q0y.png)

**SMURFS** (**SM**art **U**se**R** **F**requency analy**S**er) is a simple program, that allows for a quick statistical analysis of variable stars 
using the LombScargle algorithm. It also allows for "splitting" such a dataset into equally sized chunks, to perform a 
time dependend analysis of the frequencies.

SMURFS is developed in Python3, using optimized scientific libraries like [numpy](http://www.numpy.org/), 
[scipy](https://www.scipy.org/) and [astropy](http://www.astropy.org/).

## Prerequisits
It is assumed that *git*,*python3* and *pip* are installed. If not, follow the installation instructions for 
[git](https://git-scm.com/), [python](https://www.python.org/) and [pip](https://pip.pypa.io/en/stable/installing/).

## Installation
It is recommended to create a new virtualenvironment.
```
cd SMURFS/
python3 -m venv venv/
source venv/bin/activate
```
Afterwarts, simply install it using pip
```
pip install smurfs
```
## Usage
Activate the virtualenvironment
```
cd SMURFS/
source venv/bin/activate
```
There are two ways to access SMURFS. The recommended version is using
it as a module, as you can call this at any place on your computer:
```
python -m smurfs
```

You can also use it via main.py
```
python __main.py__
```

All possible commandline parameters can be accessed using the help flag
```
python -m smurfs -h
```
At least you need to provide the fileName, signal to noise ratio and windowsize. For example
```
python -m smurfs tests/testFile.dat 4 2
```
To define chunks provide the timerangesplit and overlap parameters.
## Output and results
All results will be written to the _results/_ path relative to the 
path where you have called SMURFS.The analysis will generate 3 
different outputs for each run:
* A folder, named after the timerange chosen, containing plots of the 
spectra and a txt file containing the data of the spectrum.
* A Spectrogram plot named **dynamic_fourier.png**
* A file called _results.txt_, containing all significant frequencies.

## Commandline parameters

All commandline parameters are available through the -h flag
when calling smurfs
```
python -m smurfs -h
```
The following are the current possibilities, including 
small examples.

### Mandatory parameters
* **fileName**: First parameter, containing the relative
path to the file containing the data.
* **snr**: Signal to noise ratio, used as a cutoff criterion. Will
try to find all significant frequencies up to this ratio.
* **windowSize**: Defines the size of the box, where the snr is 
calculated. The middlepoint of this box will be the frequency 
for which the snr is calculated. This is of course an approximation
and uses the nearest point to the edges of the box as the real 
window.

Example:
```
python -m smurfs tests/testFile.dat 4 2
``` 

### Optional parameters
* **_-fr_ or _--frequencyRange_**: Defines the frequency range
where the algorithm will perform the analysis. By default it 
will calculate all frequencies from 0 to the nyquist frequency.
It is possible to go above the nyquist frequency with this parameter
and perform a super nyquist analysis.
```
python -m smurfs tests/testFile.dat 4 2 -fr=30,50
```
* **_-trs_ or _--timeBaseSplit_**: With this parameter, the data can be
split into time chunks, where as for each chunk the analysis is performed
and results are generated. For example, lets assume the dataset is 200 days.
A timeBaseSplit of 50, would split the data into 4 parts: _0-50, 50-100,
 100-150 and 150 to 200_. 
```
python -m smurfs tests/testFile.dat 4 2 -trs=50
```
* **_-o_ or _--overlap_**: This parameter allows for an overlap of the time chunks
generated by _-trs_. For example, lets again assume the dataset is 200 days and 
we have set the split at 50. With an Overlap of 10 days, the chunks would split the
data this way: _0-50,40-90,80-130,120-170_. Be aware, that the last chunk 
will not have the full analyse the full dataset for this option, as the last
chunk wouldn't fullfill the 50 day criterion.
```
python -m smurfs tests/testFile.dat 4 2 -trs=50 -o=10
```
* **_-om_ or _--outputMode_**: This parameter defines the output content
of the analysis. With the option _Full_, all amplitude spectra will be exported and saved.
With the option _Normal_, which is the default behaviour, only the first and last
amplitude spectra will be saved.
```
python -m smurfs tests/testFile.dat 4 2 -om=Full
```
* **_-fm_ or _--frequencyMarker_**: This parameter allows for the adding of markers
to the spectrogram plot, which is generated from the analysis. It should point to a file
containing the markers, with the first row containing its names and the second row containing 
the according values. Be aware, that if you set the _-fr_ option, the spectrogram will not 
necessarily contain all lines. For example, if your lowest marker is at 40 c/d, and you have
set _-fr=45,70_, the range between 40 and 45 will not be plotted, but will be visible as an
empty area.
```
python -m smurfs tests/testFile.data 4 2 -fm=tests/test_frequencyMarker.txt
```
* **_--version_**: Shows the current version of SMURFS



## Features

SMURFS provides various nice to have features, setting it apart
from common frequency analysers. These include

* Python only. No more Fortran, IDL or other more obfuscating languages 
* Fast runs due to the usage of optimized libraries, including numpy, scipy and astropy,
dedicated to scientific work
* Generates a full result set that can be used for further analysis, including 
spectra of the first and last frequency, spectrograms, machine readable results and so on.
