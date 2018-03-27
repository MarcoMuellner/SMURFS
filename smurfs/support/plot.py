import warnings
warnings.simplefilter(action='ignore',category=FutureWarning)
from plotnine import *
import pandas as pd
from smurfs.support import *

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
