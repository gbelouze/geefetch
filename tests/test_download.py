from collections.abc import Generator
from pathlib import Path

import geopandas as gpd
import pytest
import rasterio as rio
from omegaconf import DictConfig, OmegaConf

from geefetch.cli.download_implementation import (
    download_custom,
    download_dynworld,
    download_gedi,
    download_landsat8,
    download_nasadem,
    download_palsar2,
    download_s1,
    download_s2,
)
from geefetch.cli.omegaconfig import load
from geefetch.data.process import tif_is_clean
from geefetch.utils.enums import CompositeMethod, P2Orbit, S1Orbit


@pytest.fixture
def paris_config_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Generator[Path]:
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_id = gee_project_id

    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    yield conf_path
    conf_path.unlink()


@pytest.fixture
def paris_timeseriesconfig_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Path:
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_id = gee_project_id
    raw_paris_config.satellite_default.composite_method = CompositeMethod.TIMESERIES

    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


@pytest.fixture
def paris_config_selected_bands_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Path:
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_id = gee_project_id
    raw_paris_config["s1"] = {"selected_bands": ["VV", "VH", "angle"]} | dict(
        raw_paris_config.get("s1", {})
    )
    raw_paris_config["gedi"] = {"selected_bands": ["rh95", "rh98"]} | dict(
        raw_paris_config.get("gedi", {})
    )

    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


@pytest.fixture
def paris_config_tile_range_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Path:
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_id = gee_project_id
    raw_paris_config.satellite_default.aoi.spatial.right = 660001
    raw_paris_config["s1"] = {"tile_range": (0.5, 1.)} | dict(raw_paris_config.get("s1", {}))
    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


class TestDownloadSentinel1:
    @pytest.fixture(params=list(S1Orbit), ids=lambda x: f"s1_orbit={x.value}")
    def paris_config_path_all_s1_orbits(self, request, paris_config_path: Path):
        config = OmegaConf.load(paris_config_path)
        config["s1"] = {"orbit": request.param} | dict(config.get("s1", {}))
        paris_config_path.write_text(OmegaConf.to_yaml(config))
        return paris_config_path

    @pytest.fixture(
        params=[
            None,
            "France",
            "Germany",
            ["France", "Germany"],
        ],
        ids=[None, "France", "Germany", "France & Germany"],
    )
    def paris_config_path_0_1_or_more_countries(self, request, paris_config_path: Path):
        config = OmegaConf.load(paris_config_path)
        config.satellite_default.aoi.country = request.param
        paris_config_path.write_text(OmegaConf.to_yaml(config))
        return paris_config_path

    def test_download_s1(self, paris_config_path_all_s1_orbits: Path):
        download_s1(paris_config_path_all_s1_orbits)
        conf = load(paris_config_path_all_s1_orbits)
        downloaded_files = list(Path(conf.data_dir).rglob("*.tif"))
        assert len(downloaded_files) == 1
        assert downloaded_files[0].parts[-2:] == ("s1", "s1_EPSG2154_650000_6860000.tif")

    def test_download_timeseries_s1(self, paris_timeseriesconfig_path: Path):
        download_s1(paris_timeseriesconfig_path)
        conf = load(paris_timeseriesconfig_path)
        downloaded_files = sorted(list(Path(conf.data_dir).rglob("*.tif")))
        assert len(downloaded_files) == 5
        assert downloaded_files[0].parts[-3:] == (
            "s1",
            "s1_EPSG2154_650000_6860000",
            "S1A_IW_GRDH_1SDV_20200111T174030_20200111T174055_030756_0386DC_869A.tif",
        )

    def test_download_s1_overwrite_garbage(self, paris_config_path: Path):
        conf = load(paris_config_path)
        downloaded_tif_path = Path(conf.data_dir) / "s1" / "s1_EPSG2154_650000_6860000.tif"
        downloaded_tif_path.parent.mkdir()
        downloaded_tif_path.write_text("Garbage content")
        download_s1(paris_config_path)
        downloaded_files = list(Path(conf.data_dir).rglob("*.tif"))
        assert len(downloaded_files) == 1
        assert downloaded_files[0].parts[-2:] == ("s1", "s1_EPSG2154_650000_6860000.tif")
        assert tif_is_clean(downloaded_tif_path)

    def test_select_bands_s1(self, paris_config_selected_bands_path: Path):
        download_s1(paris_config_selected_bands_path)
        conf = load(paris_config_selected_bands_path)
        downloaded_path = next(iter((Path(conf.data_dir) / "s1").glob("s1*.tif")))
        with rio.open(downloaded_path) as ds:
            assert ds.count == 3
            for target_band_name, band_idx in zip(["VV", "VH", "angle"], range(1, 4), strict=True):
                band_tags = ds.tags(band_idx)
                band_name = band_tags.get("name", f"Unknown name for band {band_idx}")
                assert target_band_name == band_name

    def test_select_0_1_or_many_countries(self, paris_config_path_0_1_or_more_countries: Path):
        download_s1(paris_config_path_0_1_or_more_countries)
        conf = load(paris_config_path_0_1_or_more_countries)
        downloaded_files = list(Path(conf.data_dir).rglob("*.tif"))
        country = conf.satellite_default.aoi.country
        if country == "Germany":
            assert len(downloaded_files) == 0
        else:
            assert len(downloaded_files) == 1
            assert downloaded_files[0].parts[-2:] == ("s1", "s1_EPSG2154_650000_6860000.tif")

    def test_download_s1_tile_range(self, paris_config_tile_range_path: Path):
        download_s1(paris_config_tile_range_path)
        conf = load(paris_config_tile_range_path)
        downloaded_files = list(Path(conf.data_dir).rglob("*.tif"))
        assert len(downloaded_files) == 1
        assert downloaded_files[0].parts[-2:] == ("s1", "s1_EPSG2154_660000_6860000.tif")


class TestDownloadGedi:
    def test_download_gedi_vector(self, paris_config_path: Path):
        download_gedi(paris_config_path, vector=True)
        conf = load(paris_config_path)
        downloaded_files = sorted(list(Path(conf.data_dir).rglob("*.parquet")))
        assert len(downloaded_files) == 2
        assert downloaded_files[0].parts[-2:] == (
            "gedi_vector",
            "gedi_vector_EPSG2154_650000_6860000.parquet",
        )

    def test_select_bands_gedi_vector(self, paris_config_selected_bands_path: Path):
        download_gedi(paris_config_selected_bands_path, vector=True)
        conf = load(paris_config_selected_bands_path)
        downloaded_path = next(iter((Path(conf.data_dir) / "gedi_vector").glob("gedi_*.parquet")))
        gdf = gpd.read_parquet(downloaded_path)
        assert gdf.columns.to_list() == ["id", "rh95", "rh98", "geometry"]


@pytest.mark.slow
class TestDownloadOtherSatellites:
    def test_download_s2(self, paris_config_path: Path):
        download_s2(paris_config_path)

    def test_download_timeseries_s2(self, paris_timeseriesconfig_path: Path):
        download_s2(paris_timeseriesconfig_path)

    def test_download_dynworld(self, paris_config_path: Path):
        download_dynworld(paris_config_path)

    def test_download_timeseries_dynworld(self, paris_timeseriesconfig_path: Path):
        download_dynworld(paris_timeseriesconfig_path)

    def test_download_timeseries_gedi_vector(self, paris_timeseriesconfig_path: Path):
        download_gedi(paris_timeseriesconfig_path, vector=True)

    def test_download_gedi_raster(self, paris_config_path: Path):
        download_gedi(paris_config_path, vector=False)

    def test_download_timeseries_gedi_raster(self, paris_timeseriesconfig_path: Path):
        download_gedi(paris_timeseriesconfig_path, vector=False)

    def test_download_landsat8(self, paris_config_path: Path):
        download_landsat8(paris_config_path)

    def test_download_timeseries_landsat8(self, paris_timeseriesconfig_path: Path):
        download_landsat8(paris_timeseriesconfig_path)

    @pytest.fixture(params=list(P2Orbit), ids=lambda x: f"palsar_orbit={x.value}")
    def paris_config_path_all_palsar_orbits(self, request, paris_config_path: Path):
        config = OmegaConf.load(paris_config_path)
        config.palsar2.orbit = request.param
        paris_config_path.write_text(OmegaConf.to_yaml(config))
        return paris_config_path

    def test_download_palsar2(self, paris_config_path_all_palsar_orbits: Path):
        download_palsar2(paris_config_path_all_palsar_orbits)
        conf = load(paris_config_path_all_palsar_orbits)
        downloaded_files = list(Path(conf.data_dir).rglob("*.tif"))
        assert len(downloaded_files) == 1

    def test_download_timeseries_palsar2(self, paris_timeseriesconfig_path: Path):
        download_palsar2(paris_timeseriesconfig_path)

    def test_download_nasadem(self, paris_config_path: Path):
        download_nasadem(paris_config_path)

    def test_download_timeseries_nasadem(self, paris_timeseriesconfig_path: Path):
        with pytest.raises(ValueError, match="Time series is not relevant for DEM."):
            download_nasadem(paris_timeseriesconfig_path)

    def test_download_custom_chm_pauls(self, paris_config_path):
        download_custom(paris_config_path, "chm_pauls")
        conf = load(paris_config_path)
        downloaded_files = list(Path(conf.data_dir).rglob("*.tif"))
        assert len(downloaded_files) == 1
