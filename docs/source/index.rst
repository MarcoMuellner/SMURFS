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
information on what SMURFS is all about, check the :ref:`About SMURFS page<About SMURFS>`.

After this, you might be interested on how SMURFS actually works. A good starting point here are the various
class documentations, that give you a full documentation of the necessary classes to start a SMURFS run. They describe
each class in detail. The :ref:`Internals page<Internals>` also gives you some details on how SMURFS
internally works.

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   getting_started/about
   getting_started/installation
   getting_started/quickstart
   getting_started/terminal

.. toctree::
   :maxdepth: 1
   :caption: Important classes

   class_doc/smurfs
   class_doc/ffinder
   class_doc/frequency
   class_doc/periodogram
   class_doc/inner_workings.rst

.. toctree::
   :maxdepth: 1
   :caption: Examples

Index and search function
-------------------------

:ref:`genindex`

:ref:`search`