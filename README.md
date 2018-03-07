# SMURFS ![Travis Status](https://travis-ci.com/muma7490/smurf.svg?token=8v1in8xqWD2uEu8JH1Q7&branch=master)
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
To use SMURFS, simply clone the repository with
```
git clone https://github.com/muma7490/SMURFS/
```
It is recommended to create a new virtualenvironment.
```
cd SMURFS/
python3 -m venv venv/
source venv/bin/activate
```
Afterwards install all necessary packages using pip
```
pip install -r requirements.txt
```
And you are set to go.

## Usage
All possible commandline parameters can be accessed using the help flag
```
python main.py -h
```
At least you need to provide the fileName, signal to noise ration and windowsize. For example
```
python main.py tests/testFile.dat 4 2
```
To define chunks provide the timerangesplit and overlap parameters.
