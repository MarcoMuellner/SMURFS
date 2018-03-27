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
At least you need to provide the fileName, signal to noise ration and windowsize. For example
```
python -m smurfs tests/testFile.dat 4 2
```
To define chunks provide the timerangesplit and overlap parameters.
