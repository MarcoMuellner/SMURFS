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
## Documentation

Full documenation is available [here](https://smurfs.readthedocs.io/en/master/)

## Features

SMURFS provides various nice to have features, setting it apart
from common frequency analysers. These include

* Python only. No more Fortran, IDL or other more obfuscating languages 
* Fast runs due to the usage of optimized libraries, including numpy, scipy and astropy,
dedicated to scientific work
* Generates a full result set that can be used for further analysis, including 
spectra of the first and last frequency, spectrograms, machine readable results and so on.
