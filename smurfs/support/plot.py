import warnings
warnings.simplefilter(action='ignore',category=FutureWarning)
from plotnine import *
import numpy as np
import pandas as pd
from smurfs.support import *
import matplotlib.pyplot as pl
from matplotlib.colors import Colormap

@timeit
def plotCustom(title, data, **kwargs):
    p = ggplot()
    for name,(data,linestyle,linetype) in data.items():
        linetype = 'solid' if linetype is None else linetype
        try:
            plotData = pd.DataFrame({'x':data[0],'y':data[1],'Legend':[name]*len(data[0])})
        except IndexError:
            plotData = pd.DataFrame({'x': data, 'Legend': [name]})
        if linestyle == geom_point:
            p = p+linestyle(aes(x='x',y='y',color='Legend'),data=plotData)
        elif linestyle == geom_vline:
            p = p+linestyle(aes(xintercept='x',color='Legend'),data=plotData)
        else:
            p = p + linestyle(aes(x='x', y='y', color='Legend'), data=plotData,linetype=linetype)

    p = p+ggtitle(title)+xlab(kwargs['xLabel'])+ylab(kwargs['yLabel'])
    return p


def plotMesh(f,t,i):
    pl.pcolormesh(f, t, i,cmap="inferno")
    pl.xlabel(r"Frequency")
    pl.ylabel(r"Time")
    pl.colorbar()
    np.savetxt("frequency.txt",f)
    np.savetxt("time.txt", t)
    np.savetxt("intensity.txt", i)
    pl.savefig("results/dynamic_fourier.png")