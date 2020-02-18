About SMURFS
============

Functionality
-------------
At its heart, SMURFS is a tool designed to extract significant frequencies from a time series in a fully automated way.
SMURFS can be very easy to use, and give you quick insight into the data. It is also designed to be as configurable
as one wants it to be, and it is possible to drill down to the individual frequencies.

In its simplest form, one only needs to provide a name of a star that is observed by the missions supported by SMURFS
(e.g. TESS, Kepler, K2), the minimum Signal to Noise Ratio (SNR, being the ratio of the signals amplitude and the mean
of the surrounding area in the amplitude spectrum) and the window size (defining the area around the peak, which SMURFS
considers as a proxy for noise).

But what if i want to do a deeper analysis? SMURFS has you covered there as well and has loads of configurability and
settings, allowing you to take a deeper look. For example, SMURFS can download/extract different data products, with
different amount or reduction applied. You can specify, how the frequencies are fitted to the data, you can look at
specific frequency ranges, you can fold and flatten your light curves and much more.

To get you started, you should first check the :ref:`installation page <Installation and requirements>`, to make sure you have all
prerequisites installed. Afterwards, take a look at the :ref:`quickstart <Quickstart>` page, giving you a first easy example.
Afterwards, feel free to roam this documentation and check out the different possibilities you have with SMURFS.

References and links
--------------------
Of course, SMURFS wasn't built in a vacuum. Check out these amazing packages on which SMURFS is built on:

- **`Lightkurve <https://docs.lightkurve.org/>`_**: Lightkurve is the heart and soul of all time series/periodogram
  objects in SMURFS. Therefore you can use the whole Lightkurve API on these types of objects
  (for example: *Smurfs.lc*, *Smurfs.pdg*).`Here <https://docs.lightkurve.org/api/lightkurve.lightcurve.LightCurve.html#lightkurve.lightcurve.LightCurve>`_
  is a link to the API for LightCurve objects for example.
- **`Eleanor <https://github.com/afeinstein20/eleanor>`_**: Eleanor is a python package, that allows for extraction
  of long cadence light curves from TESS FFIs.