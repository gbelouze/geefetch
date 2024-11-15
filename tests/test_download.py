from pathlib import Path
import pytest

from geefetch.cli.download_implementation import (
    download_dynworld,
    download_gedi,
    download_landsat8,
    download_palsar2,
    download_s1,
    download_s2,
)


def test_download_s1(paris_config_path: Path):
    download_s1(paris_config_path)


@pytest.mark.slow
def test_download_s2(paris_config_path: Path):
    download_s2(paris_config_path)


@pytest.mark.slow
def test_download_dynworld(paris_config_path: Path):
    download_dynworld(paris_config_path)


@pytest.mark.slow
def test_download_gedi_vector(paris_config_path: Path):
    download_gedi(paris_config_path, vector=True)


@pytest.mark.slow
def test_download_gedi_raster(paris_config_path: Path):
    download_gedi(paris_config_path, vector=False)


@pytest.mark.slow
def test_download_landsat8(paris_config_path: Path):
    download_landsat8(paris_config_path)


@pytest.mark.slow
def test_download_palsar2(paris_config_path: Path):
    download_palsar2(paris_config_path)
