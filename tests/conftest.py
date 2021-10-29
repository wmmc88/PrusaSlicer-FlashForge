import pytest

from pathlib import Path

@pytest.fixture()
def test_data_path(monkeypatch) -> Path:
    return (Path(__file__)/'..'/'data').resolve(strict=True)

@pytest.fixture(autouse=True)
def default_test_env(monkeypatch, test_data_path):
    monkeypatch.setenv(name='SLIC3R_PP_OUTPUT_NAME', value=str(test_data_path/'generated_test_output.g'))
    monkeypatch.setenv(name='SLIC3R_TRAVEL_SPEED', value='130')
    monkeypatch.setenv(name='SLIC3R_TRAVEL_SPEED_Z', value='7')

