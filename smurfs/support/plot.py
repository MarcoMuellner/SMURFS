import warnings
warnings.simplefilter(action='ignore',category=FutureWarning)
import os
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


def plotMesh(f,t,i,**kwargs):
    fig = pl.figure()
    ax1 = fig.add_subplot(111)
    if "minimumIntensity" in kwargs.keys():
        mappable = ax1.pcolormesh(f, t, i,cmap="gnuplot"
                                  ,vmin=kwargs["minimumIntensity"],vmax=np.amax(i))
    else:
        mappable = ax1.pcolormesh(f, t, i, cmap="gnuplot")

    if "tMax" in kwargs.keys():
        ax1.set_ylim(0,kwargs["tMax"])
    ax1.set_xlabel(r"Frequency")
    ax1.set_ylabel(r"Time")

    if "frequencyList" in kwargs.keys() and kwargs["frequencyList"] is not None:
        ax2 = ax1.twiny()
        ax3 = ax1.twiny()

        fVal = list(kwargs["frequencyList"].values())
        names = list(kwargs["frequencyList"].keys())
        minX,maxX = min(fVal),max(fVal)

        fVal2 = fVal[::2]
        names2 = names[::2]

        fVal = [x for x in fVal if x not in fVal2]
        names = [x for x in names if x not in names2]

        ax2.set_xticks(fVal)
        ax2.set_xticklabels(names)
        ax2.tick_params(labelrotation=90)

        ax3.set_xticks(fVal2)
        ax3.set_xticklabels(names2)
        ax3.tick_params(pad=20,labelrotation=90)

        ax1.set_xlim(minX*0.95,maxX*1.05)
        ax2.set_xlim(minX* 0.95, maxX * 1.05)
        ax3.set_xlim(minX * 0.95, maxX * 1.05)

    np.savetxt("frequency.txt",f)
    np.savetxt("time.txt", t)
    np.savetxt("intensity.txt", i)

    if not os.path.exists("results"):
        os.mkdir("results")
    try:
        fig.savefig("results/dynamic_fourier.png")
    except:
        print(term.format("Failed to plot dynamic fourier plot! Maybe only one timerange?",
                          term.Color.YELLOW))
