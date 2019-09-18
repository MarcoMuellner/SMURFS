Standalone usage
================

When installing Smurfs, it automatically installs a standalone version of this
code, which you can then call from the terminal. The usage is similar to what
is available, when integrating Smurfs into external scripts.

Basic usage
-----------
At the minimum, you need to provide **target**, **snr** and **window_size**
to smurfs. Target can be any name (resolvable by Simbad) of a star that
has been observed by TESS or Kepler, or the path to a file containing
a light curve. The first argument is always the target, the second the SNR and
the third window size.

.. code-block:: guess
    smurfs tests/test_files/testFile.dat 4 2

.. code-block:: guess
    smurfs "Beta Pictoris" 4 2

The code then shows you the progress of the analysis:

.. image:: https://raw.githubusercontent.com/EnricoCorsaro/DIAMONDS/master/docs/figures/DIAMONDS_LOGO_WHITE.png

