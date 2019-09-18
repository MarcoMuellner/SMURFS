Welcome to SMURFS's documentation!
==================================

**SMURFS** (**SM** art **U** se **R** **F** requency analy **S** er) is a simple program, that allows for a quick statistical analysis of variable stars
using the LombScargle algorithm. It also allows for "splitting" such a dataset into equally sized chunks, to perform a
time dependend analysis of the frequencies.

SMURFS is developed in Python3, using optimized scientific libraries like numpy (http://www.numpy.org/),
scipy (https://www.scipy.org/) and astropy (http://www.astropy.org/).

Prerequisits
------------

It is assumed that *git* , *python3* and *pip* are installed. If not, follow the installation instructions for
git (https://git-scm.com/), python (https://www.python.org/) and pip (https://pip.pypa.io/en/stable/installing/).

Installation
------------

It is recommended to create a new virtual environment.

.. code-block:: guess

    cd SMURFS/
    python3 -m venv venv/
    source venv/bin/activate

Afterwarts, simply install it using pip

.. code-block:: guess

    pip install smurfs


Usage
-----

Smurfs can be both used as a standalone software, called from the Terminal, or
embedded in external Python code. Below you can find both approaches.

.. toctree::
   :maxdepth: 3

   example
   terminal
   api
