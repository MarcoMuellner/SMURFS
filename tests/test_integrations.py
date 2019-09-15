import pytest
from lightkurve import search_lightcurvefile
from smurfs.smurfs.frequency_finder import FFinder,sin,sin_multiple
from smurfs.smurfs.smurfs import Smurfs
from smurfs.preprocess.tess import download_lc
import numpy as np

@pytest.mark.skip(reason="Temporary Skip")
def testffinder():
    s = Smurfs(file='testFile.dat')
    s.run(4,f_min=15,skip_similar=True)
    #ff.plot(show=True)
    s.plot_pdg(show=True)
    print(s.result)

@pytest.mark.skip(reason="Temporary Skip")
def testCreatedSin():
    x = np.linspace(0, 100, num=5000)
    params = [0.6,0.2,0,0.1,6,0,10,5,6]
    y = sin_multiple(x,*params) + np.random.normal(0,0.3,len(x))
    s = Smurfs(time=x, flux=y, label='test_sin')
    s.run(4,extend_frequencies=5)
    pass
