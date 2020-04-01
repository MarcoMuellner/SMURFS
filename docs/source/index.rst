Smurfs - frequency analysis made easy
=====================================
.. image:: https://i.imgur.com/Uh2UhpZ.png
   :width: 600

**SMURFS** provides a fully automated way to extract frequencies from
timeseries data sets. It provides various interfaces, from a standalone command line tool, to jupyter and python
integrations and computes possible frequency combinations, directly downloads and reduces (if necessary) data
of TESS/Kepler/K2 observations and much much more.

You can use SMURFS both integrated in your code, as well as a stand-alone product in the terminal. After checking
:ref:`installation page <Installation and requirements>`, you can take a look at the
:ref:`quickstart page <Quickstart>`, which gives you the easiest possible example on how to use SMURFS.
For more detail on the usage as a stand-alone product, :ref:`standalone settings page<Standalone settings>`. For more
information on what SMURFS is all about, check the :ref:`About SMURFS page<About SMURFS>`. SMURFS also gives you
an interactive mod to work with SMURFS. Its basic usage is described in the
:ref:`Interactive Mode page<Interactive Mode>`.


After this, you might be interested on how SMURFS actually works. A good starting point is the
:ref:`Internals page<Internals>`, which shows you how SMURFS gets to its result. It should also give you a basic
idea on the different classes. The most important ones are described in the various class documentation pages, which
documents all the different classes. If you are interested on how SMURFS downloads data sets and reduces them, check
the :ref:`downloads page<Downloading and reducing data>`.

SMURFS also allows you for vastly more advanced usage of its internals. The advanced examples page shows you some
of those in jupyter notebooks. However, you can apply the same procedures in the interactive mode.

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   getting_started/about
   getting_started/installation
   getting_started/quickstart
   getting_started/interactive_mode
   getting_started/terminal

.. toctree::
   :maxdepth: 1
   :caption: Important classes

   class_doc/inner_workings
   class_doc/data_download
   class_doc/smurfs
   class_doc/ffinder
   class_doc/frequency
   class_doc/periodogram
   class_doc/other_functions

.. toctree::
   :maxdepth: 1
   :caption: Advanced examples

   examples/downloading_data
   examples/plotting_things
   examples/fullframe_sc_data

Index and search function
-------------------------

:ref:`genindex`

:ref:`search`