import lightkurve as lk
from matplotlib.axes import Axes

class LightCurve(lk.LightCurve):
    """
     Custom LightCurve object. Reimplements the plot routine, as we only use mag within SMURFS.
     Inherits from lightkurve's LightCurve class.

     :param data: Data to initialize the light curve. Can be a lightkurve LightCurve object or compatible data.
     :param args: Additional positional arguments passed to the parent class.
     :param kwargs: Additional keyword arguments passed to the parent class.
     """
    def __init__(self, data=None, *args, **kwargs):
        if isinstance(data, lk.LightCurve):
            # If data is already a LightCurve object, we initialize from its data
            super().__init__(time=data.time, flux=data.flux, flux_err=data.flux_err, meta=data.meta)
            # Copy over any additional attributes that might be specific to TESS
            for attr in ['sector', 'camera', 'ccd', 'ra', 'dec']:
                if hasattr(data, attr):
                    setattr(self, attr, getattr(data, attr))
        else:
            # Otherwise, initialize normally
            super().__init__(data, *args, **kwargs)

    def plot(self, **kwargs):
        ax: Axes = super().plot(color='k', ylabel="Flux [mag]", normalize=False, **kwargs)
        ax.set_ylim(ax.get_ylim()[::-1])
        return ax

    def scatter(self, **kwargs):
        ax: Axes = super().scatter(color='k', ylabel="Flux [mag]", normalize=False, **kwargs)
        ax.set_ylim(ax.get_ylim()[::-1])
        return ax