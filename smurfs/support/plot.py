import warnings
warnings.simplefilter(action='ignore',category=FutureWarning)
from smurfs.support import *
import matplotlib.pyplot as pl
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
from matplotlib.colors import Colormap

pl.rc('font', family='serif')
pl.rc('xtick', labelsize='x-small')
pl.rc('ytick', labelsize='x-small')

@timeit
def plotCustom(title : str, data : np.ndarray, **kwargs) -> Figure:
    fig: Figure = pl.figure()
    ax: Axes = fig.add_subplot(111)

    dotList = ['x', 'o']
    lineStyleList = ['-', '--', '-.', ':']

    for name,(data,linestyle) in data.items():
        if linestyle in dotList:
            ax.plot(data[0], data[1],linestyle,label=name,markersize=3,color='k')
        elif linestyle in lineStyleList:
            ax.plot(data[0], data[1], linestyle = linestyle, label=name,linewidth = 1,color='k')
        elif linestyle == '|':
            ax.axvline(x=data,linestyle='--',label=name,linewidth = 1,color='blue')
        elif linestyle == '/':
            ax.axhline(y=data,linestyle='--',label=name,linewidth = 1,color='red')
        else:
            ax.plot(data[0],data[1],label=name)

    ax.set_title(title)
    if 'xLabel' in kwargs.keys():
        ax.set_xlabel(kwargs['xLabel'])

    if 'yLabel' in kwargs.keys():
        ax.set_ylabel(kwargs['yLabel'])
    return fig


def plotMesh(f,t,i,**kwargs):
    fig = pl.figure()
    ax1 = fig.add_subplot(111)
    if "minimumIntensity" in kwargs.keys():
        ax1.pcolormesh(f, t, i,cmap="gnuplot"
                                  ,vmin=kwargs["minimumIntensity"],vmax=np.amax(i))
    else:
        ax1.pcolormesh(f, t, i, cmap="gnuplot")

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

    np.save("frequency.npy",f)
    np.save("time.npy", t)
    np.save("intensity.npy", i)

    if not os.path.exists("results"):
        os.mkdir("results")
    try:
        fig.savefig("dynamic_fourier.png")
    except:
        print(term.format("Failed to plot dynamic fourier plot! Maybe only one timerange?",
                          term.Color.YELLOW))
