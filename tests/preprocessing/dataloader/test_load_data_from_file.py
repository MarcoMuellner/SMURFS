import pytest
import numpy as np
from pathlib import Path
from lightkurve import LightCurve
from smurfs.smurfs_common.preprocessing.dataloader import load_data_from_file, FluxType

# Mock the mprint function to avoid printing during tests
from unittest.mock import patch
@pytest.fixture(autouse=True)
def mock_mprint():
    with patch('smurfs.smurfs_common.preprocessing.dataloader.mprint'):
        yield

# Configure the test file
@pytest.fixture(scope="module")
def test_file():
    return Path(__file__).parent.parent.parent / "test_files" / "testFile.dat"

def test_load_data_from_file_basic(test_file):
    lc = load_data_from_file(test_file)
    assert isinstance(lc, LightCurve)
    assert len(lc.time) > 0
    assert lc.flux is not None
    assert lc.flux_err is not None

def test_load_data_from_file_apply_correction(test_file):
    lc = load_data_from_file(test_file, apply_file_correction=True)
    assert isinstance(lc, LightCurve)
    assert lc.flux.unit == 'mag'
    assert np.isclose(np.median(lc.flux.value), 0, atol=1e-10)

def test_load_data_from_file_no_correction(test_file):
    lc = load_data_from_file(test_file, apply_file_correction=False)
    assert isinstance(lc, LightCurve)
    # Check if the flux is not in magnitudes (assuming original data is not in magnitudes)
    assert np.max(np.abs(lc.flux.value)) > 10 or np.abs(np.median(lc.flux.value)) > 1

def test_load_data_from_file_nonexistent():
    with pytest.raises(FileNotFoundError):
        load_data_from_file(Path("nonexistent_file.dat"))

def test_load_data_from_file_clip_and_iterations(test_file):
    lc = load_data_from_file(test_file, clip=3, it=2, apply_file_correction=True)
    assert isinstance(lc, LightCurve)
    # Additional assertions can be added here to check the effects of clipping and iterations

def test_load_data_from_file_data_integrity(test_file):
    lc = load_data_from_file(test_file)
    # Load the data manually to compare
    raw_data = np.loadtxt(test_file)
    if raw_data.shape[0] > raw_data.shape[1]:
        raw_data = raw_data.T
    assert np.allclose(lc.time.value, raw_data[0])
    assert np.allclose(lc.flux.value, raw_data[1])
    if raw_data.shape[0] == 3:
        assert np.allclose(lc.flux_err.value, raw_data[2])

# You can add more tests as needed for specific requirements or edge cases