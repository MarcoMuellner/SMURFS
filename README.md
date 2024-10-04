# SMURFS
![SMURFS Image](https://i.imgur.com/Uh2UhpZ.png)

**SMURFS** provides automatic extraction of frequencies from
timeseries. It provides various interfaces, from a standalone command line tool, to jupyter and python 
integrations and computes possible frequency combinations, directly downloads and reduces (if necessary) data 
of TESS/Kepler/K2 observations and much much more.Smart UseR Frequency analySer
## Getting started

To install smurfs, you need python > 3.5, pip as well as cmake. If you don't have these, install them through the
packet manager of your choice (f.e. _brew_(Mac) or _apt_ (Debian)). For pip check 
[here](https://pip.pypa.io/en/stable/installing/).

## Installation

First off, create a virtual environment

```bash
cd /Path/
python3 -m venv venv/
source venv/bin/activate
```

Install smurfs through pip

```bash
pip install smurfs
```

## Quickstart

Using SMURFS as a standalone command line tool is very simple. Simply call ```smurfs``` with a **target**, signal to noise
ratio cutoff and the window size. The target can be either:

- A path to a file, containing 2 columns with time and flux
- Any name of a star, that is resolvable by Simbad and has been observed by the **Kepler**,**K2** or **TESS** missions.

As an example, we can take a look at the star Gamma Doradus:
```
smurfs "Gamma Doradus" 4 2
```

SMURFS creates a result folder after running the code. In this case it has the following structure
```
- Gamma_Doradus
    - data
        - _combinations.csv
        - _result.csv
        - LC_residual.txt
        - LC.txt
        - PS_residual.txt
        - PS.txt         
    - plots
        - LC_residual.pdf
        - LC.pdf
        - PS_residual.pdf
        - PS_result.pdf
        - PS.pdf
```
The ```LC*.txt``` files contain the light curves, original and residual. The ```PS*.txt``` files contain the 
original as well as the residual amplitude spectrum. ```_combinations.csv``` shows all combination frequencies for the 
result and ```_result.csv``` gives the result for a given run.

## Citing

If you use this software in your research, consider citing  it using Zenodo.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3768032.svg)](https://doi.org/10.5281/zenodo.3768032)


If you use SMURFS to extract LC data from FFIs, you should also cite the awesome people of Eleanor.

[Feinstein et al. 2019](https://ui.adsabs.harvard.edu/abs/2019PASP..131i4502F/abstract)


 
## Documentation

Full documentation is available [here](https://smurfs.readthedocs.io/en/master/)
