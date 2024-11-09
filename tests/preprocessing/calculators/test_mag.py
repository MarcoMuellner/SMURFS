import pytest
import numpy as np
from lightkurve import LightCurve
import astropy.units as u

from smurfs.smurfs_common.preprocessing.calculators import mag


@pytest.fixture
def sample_lightcurve():
    time = np.arange(0, 10, 0.1)
    flux = 1000 + 50 * np.sin(time)
    flux_err = np.random.normal(0, 5, len(time))
    return LightCurve(time=time, flux=flux, flux_err=flux_err)


def test_mag_basic_functionality(sample_lightcurve):
    result = mag(sample_lightcurve)
    assert isinstance(result, LightCurve)
    assert result.flux.unit == u.mag
    assert result.flux_err.unit == u.mag


def test_mag_normalization(sample_lightcurve):
    result = mag(sample_lightcurve)
    assert np.isclose(np.median(result.flux.value), 0, atol=1e-10)


def test_mag_with_negative_flux():
    lc = LightCurve(time=np.arange(10), flux=-100 + np.random.normal(0, 10, 10), flux_err=np.ones(10))
    result = mag(lc)
    assert np.all(np.isfinite(result.flux.value))
    assert np.all(np.isfinite(result.flux_err.value))


def test_mag_with_nans():
    flux = np.array([1000, np.nan, 1000, 1000, np.nan])
    lc = LightCurve(time=np.arange(5), flux=flux, flux_err=np.ones(5))
    result = mag(lc)
    assert len(result.flux) == 3
    assert np.all(np.isfinite(result.flux.value))


def test_mag_preserves_variability(sample_lightcurve):
    original_std = np.std(sample_lightcurve.flux.value)
    result = mag(sample_lightcurve)
    result_std = np.std(result.flux.value)
    assert np.isclose(original_std / np.mean(sample_lightcurve.flux.value),
                      result_std, rtol=1e-2)


def test_mag_with_zero_error():
    lc = LightCurve(time=np.arange(10), flux=np.ones(10) * 1000, flux_err=np.zeros(10))
    result = mag(lc)
    assert np.all(result.flux_err.value == 0)


def test_mag_with_large_values():
    lc = LightCurve(time=np.arange(10), flux=np.ones(10) * 1e20, flux_err=np.ones(10) * 1e18)
    result = mag(lc)
    assert np.all(np.isfinite(result.flux.value))
    assert np.all(np.isfinite(result.flux_err.value))
