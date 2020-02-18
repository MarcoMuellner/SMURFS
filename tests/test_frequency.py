import pytest
from lightkurve import search_lightcurvefile
from smurfs._smurfs.frequency_finder import sin_multiple,Frequency
from smurfs._smurfs.smurfs import Smurfs
from smurfs.preprocess.tess import download_lc
import numpy as np

param_list = [
    ([0.6,0.2,0],(0.6,0.2,0))
    ,([0.6,0.5,0,0.3,3,0.1],(0.6,0.5,0))
    #,([0.6,0.2,0,0.1,6,0,10,5,6],(10,5,6))
]

@pytest.mark.skip(reason="Temporary Skip")
@pytest.mark.parametrize('value',param_list)
def testFrequency(value):
    x = np.linspace(0,100,num=5000)
    noise = np.random.normal(0,0.05,len(x))
    y = sin_multiple(x, *value[0]) + noise

    f = Frequency(x,y,4,2)
    f.pre_whiten(mode='scipy')

    assert np.abs(f.amp.nominal_value - value[1][0]) < 4 * f.amp.std_dev
    assert np.abs(f.f.nominal_value - value[1][1]) < 4 * f.f.std_dev
    assert np.abs(f.phase.nominal_value - value[1][2]) < 8 * f.phase.std_dev

    f = Frequency(x, y, 4, 2)
    f.pre_whiten(mode='lmfit')

    assert np.abs(f.amp.nominal_value - value[1][0]) < 8 * f.amp.std_dev
    assert np.abs(f.f.nominal_value - value[1][1]) < 8 * f.f.std_dev
    try:
        assert np.abs(f.phase.nominal_value - value[1][2]) < 8 * f.phase.std_dev
    except AssertionError:
        assert np.abs(f.phase.nominal_value - (value[1][2] + 2 * np.pi)) < 8 * f.phase.std_dev
