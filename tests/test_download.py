from pathlib import Path

import pytest
import rasterio as rio
from omegaconf import DictConfig, OmegaConf

from geefetch.cli.download_implementation import (
    download_dynworld,
    download_gedi,
    download_landsat8,
    download_palsar2,
    download_s1,
    download_s2,
)
from geefetch.cli.omegaconfig import load


@pytest.fixture
def paris_config_all_s1_bands_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Path:
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_id = gee_project_id
    raw_paris_config.s1.selected_bands = ["VV", "VH", "angle"]

    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


def test_download_s1(paris_config_path: Path):
    download_s1(paris_config_path)


def test_download_timeseries_s1(paris_timeseriesconfig_path: Path):
    download_s1(paris_timeseriesconfig_path)


def test_select_bands_s1(paris_config_all_s1_bands_path: Path):
    download_s1(paris_config_all_s1_bands_path)
    conf = load(paris_config_all_s1_bands_path)
    downloaded_path = next(iter((Path(conf.data_dir) / "s1").glob("s1*.tif")))
    with rio.open(downloaded_path) as ds:
        assert ds.count == 3
        for target_band_name, band_idx in zip(["VV", "VH", "angle"], range(1, 4), strict=True):
            band_tags = ds.tags(band_idx)
            band_name = band_tags.get("name", f"Unknown name for band {band_idx}")
            assert target_band_name == band_name


@pytest.mark.slow
def test_download_s2(paris_config_path: Path):
    download_s2(paris_config_path)


@pytest.mark.slow
def test_download_timeseries_s2(paris_timeseriesconfig_path: Path):
    download_s2(paris_timeseriesconfig_path)


@pytest.mark.slow
def test_download_dynworld(paris_config_path: Path):
    download_dynworld(paris_config_path)


@pytest.mark.slow
def test_download_timeseries_dynworld(paris_timeseriesconfig_path: Path):
    download_dynworld(paris_timeseriesconfig_path)


def test_download_gedi_vector(paris_config_path: Path):
    download_gedi(paris_config_path, vector=True)


@pytest.mark.slow
def test_download_timeseries_gedi_vector(paris_timeseriesconfig_path: Path):
    download_gedi(paris_timeseriesconfig_path, vector=True)


@pytest.mark.slow
def test_download_gedi_raster(paris_config_path: Path):
    download_gedi(paris_config_path, vector=False)


@pytest.mark.slow
def test_download_timeseries_gedi_raster(paris_timeseriesconfig_path: Path):
    download_gedi(paris_timeseriesconfig_path, vector=False)


@pytest.mark.slow
def test_download_landsat8(paris_config_path: Path):
    download_landsat8(paris_config_path)


@pytest.mark.slow
def test_download_timeseries_landsat8(paris_timeseriesconfig_path: Path):
    download_landsat8(paris_timeseriesconfig_path)


@pytest.mark.slow
def test_download_palsar2(paris_config_path: Path):
    download_palsar2(paris_config_path)


@pytest.mark.slow
def test_download_timeseries_palsar2(paris_timeseriesconfig_path: Path):
    download_palsar2(paris_timeseriesconfig_path)
