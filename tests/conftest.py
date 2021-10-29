import pytest

from pathlib import Path


@pytest.fixture()
def test_data_path(monkeypatch) -> Path:
    return (Path(__file__) / '..' / 'data').resolve(strict=True)

@pytest.fixture(autouse=True)
def test_env(monkeypatch, test_data_path, request):
    test_name = request.param
    monkeypatch.setenv(name='SLIC3R_PP_OUTPUT_NAME', value=str(test_data_path / f'{test_name}.gcode'))
    monkeypatch.setenv(name='SLIC3R_TRAVEL_SPEED', value='130')
    monkeypatch.setenv(name='SLIC3R_TRAVEL_SPEED_Z', value='7')

    return {'test_name': test_name}
