SMURFS as a command line tool
=============================

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

The code then shows you the progress of the analysis, as well as some infos:

.. image:: https://raw.githubusercontent.com/MarcoMuellner/SMURFS/rework/docs/source/images/output.png

You can also stop this run at any time using *CTRL+C*, which saves the result
up to that point.

Parameters
----------

**Help**:
    - .. code-block:: guess

         smurfs -h
    - Shows all parameters and infos for them

**Frequency Range**:
    - .. code-block:: guess

        smurfs -fr 20,40
    - Restricts the analysis to a given frequency range

**Skip similar Frequencies**
    - .. code-block:: guess

        smurfs -ssa
    - If the analysis finds 10 consecutive frequencies within a standard deviation of 0.05, that range will be ignored for further analysis

**Skip Cutoff**
    - .. code-block:: guess

        smurfs -sc
    - Skips the cutoff check. If this is **not** set, the run will be chancelled after 10 consecutive frequencies within a standard deviation of 0.05.

**Extend frequencies**
    - .. code-block:: guess

        smurfs -ef 5
    - Extends the analysis by n insignificant frequencies, meaning the analysis will be stopped after n consecutive insignificant frequencies, instead of the first found.

**Disable Improve Frequencies**
    - .. code-block:: guess

        smurfs -dif
    - Disables the improve frequencies feature, meaning the initially fitted frequencies are kept

**Fit method**
    - .. code-block:: guess

        smurfs -fm scipy
    - Choose the fitting method, either lmfit or scipy

**Flux Type**
    - .. code-block:: guess

        smurfs -ft SAP
    - Choose the flux if a TESS SC target is chosen, either PDCSAP or SAP

**Store object**
    - .. code-block:: guess

        smurfs -so
    - Stores the smurfs object that can be loaded later

**Save path**
    - .. code-block:: guess

        smurfs -sp ../
    - Chooses the path where the results are saved

**Interactive mode**
    - .. code-block:: guess

        smurfs -i
    - Starts an iPython shell after the analysis is complete. You can then interact with the object




