Downloading and reducing data
=============================

SC data
-------

SMURFS provides various ways to access online data. The following missions are supported and can be accessed through
SMURFS:

- TESS
- Kepler
- K2

You can provide these missions either through the class interface of SMURFS, or as a setting in the standalone version
of SMURFS. In many cases, the download of data is facilitated through
`lightkurve <https://docs.lightkurve.org/api/lightkurve.search.search_lightcurvefile.html?highlight=search_lightcurvefile>`_ ,
giving you access to SC data.

SMURFS automatically removes data points with bad quality flags and nans in the flux. In general,
`lightkurve.search_lightcurvefile` provides the data in electron counts, which SMURFS converts into magnitude. Further,
it normalizes the light curve around zero by removing the median in the data and applies sigma clipping (sigma=4, iters=1)
by default. You can change this behaviour through the appropriate settings in the standalone version, or by setting
the parameters in the :meth:`smurfs.Smurfs` class.

LC data download
----------------

Seeing as the vast majority of targets in TESS are observed in the LC mode, SMURFS also provides a very simple way
to access these targets. It makes heavy use of the `eleanor <https://github.com/afeinstein20/eleanor>`_ pipeline.

If you provide a target that has been observed in TESSs LC mode, SMURFS will automatically try to resolve it through
MAST. It then will download a cutout around the target using the `TessCut <https://mast.stsci.edu/tesscut/>`_ service.
We then extract the lightcurve by using Eleanor. It automatically tries to find the best aperture around the target,
by checking apertures that have shown to work well with Kepler data. From there, the systematics are removed
from the light curve, and if the PSA flag is set (which is on by default), it applies co-trending basis vectors
to further improve the data. SMURFS also provides a validation page for each LC target, showing you how the
extraction worked.

Using internal functions
------------------------

While the interface of SMURFS is designed to be as convenient as possible, you can also choose to use the internal
functions to download data and load files. To make the code do the work, you can simply use
:meth:`smurfs.preprocess.tess.download_lc`. It has a very similar interface to the normal :meth:`smurfs.Smurfs` class.

If you are interested only in the LC data of a given target (seeing as SMURFS always uses SC data if available), you
can also use the :meth:`smurfs.preprocess.tess.cut_ffi` function. You need the TIC id of the target to run this
function. If you don't have it, you can get it using this simple snippet:

.. code-block:: python

    from astroquery.mast import Catalogs

    Catalogs.query_object(target_name,catalog='TIC',radius=0.003)[0]['ID']

If you are interested in the different observations that exist in MAST for a given target, you can use

.. code-block:: python

    from astroquery.mast import Observations

    Observations.query_criteria(objectname=target_name, radius=str(0 * u.deg), project='TESS',
                                        obs_collection='TESS')
