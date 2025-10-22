import tempfile
from collections.abc import Generator
from pathlib import Path

import geopandas as gpd
import numpy as np
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
from geefetch.cli.omegaconfig import SpeckleFilterConfig, load
from geefetch.data.process import tif_is_clean
from geefetch.utils.enums import CompositeMethod, P2Orbit, ResamplingMethod, S1Orbit


@pytest.fixture
def paris_config_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Generator[Path]:
    raw_paris_config = raw_paris_config.copy()
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_ids = [gee_project_id]

    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    yield conf_path
    conf_path.unlink()


@pytest.fixture
def paris_speckle_path(raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str):
    raw_paris_config = raw_paris_config.copy()
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_ids = [gee_project_id]
    raw_paris_config.s1.speckle_filter = SpeckleFilterConfig()
    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


@pytest.fixture
def paris_speckle_timeseries_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
):
    raw_paris_config = raw_paris_config.copy()
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_ids = [gee_project_id]
    raw_paris_config.satellite_default.composite_method = CompositeMethod.TIMESERIES
    raw_paris_config.s1.speckle_filter = SpeckleFilterConfig()
    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


@pytest.fixture
def paris_timeseriesconfig_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Path:
    raw_paris_config = raw_paris_config.copy()
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_ids = [gee_project_id]
    raw_paris_config.satellite_default.composite_method = CompositeMethod.TIMESERIES

    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


@pytest.fixture
def paris_config_selected_bands_path(
    raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str
) -> Path:
    raw_paris_config = raw_paris_config.copy()
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_ids = [gee_project_id]
    raw_paris_config["s1"] = {"selected_bands": ["VV", "VH", "angle"]} | dict(
        raw_paris_config.get("s1", {})
    )
    raw_paris_config["gedi"] = {"selected_bands": ["rh95", "rh98"]} | dict(
        raw_paris_config.get("gedi", {})
    )

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

    def test_download_s1_with_speckle_filter(self, paris_speckle_path: Path):
        download_s1(paris_speckle_path)
        conf = load(paris_speckle_path)
        downloaded_files = sorted(list(Path(conf.data_dir).rglob("*.tif")))
        assert len(downloaded_files) == 1
        assert downloaded_files[0].parts[-2:] == ("s1", "s1_EPSG2154_650000_6860000.tif")

    def test_download_s1_with_speckle_filter_and_timeseries(
        self, paris_speckle_timeseries_path: Path
    ):
        download_s1(paris_speckle_timeseries_path)
        conf = load(paris_speckle_timeseries_path)
        downloaded_files = sorted(list(Path(conf.data_dir).rglob("*.tif")))
        assert len(downloaded_files) == 5
        breakpoint()
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


class TestResamplingMethods:
    """Test that different resampling methods produce different outputs."""

    def test_resampling_methods_produce_different_outputs(self, paris_config_path: Path):
        """Test that different resampling methods produce different outputs."""

        # Create three configs with different resampling methods
        config_bilinear = OmegaConf.load(paris_config_path)
        config_nearest = OmegaConf.load(paris_config_path)
        config_bicubic = OmegaConf.load(paris_config_path)

        # Set different resampling methods
        config_bilinear.satellite_default.resampling = ResamplingMethod.BILINEAR
        config_nearest.satellite_default.resampling = ResamplingMethod.NEAREST
        config_bicubic.satellite_default.resampling = ResamplingMethod.BICUBIC

        # Create separate temporary directories for each download
        with (
            tempfile.TemporaryDirectory() as bilinear_tmp_dir,
            tempfile.TemporaryDirectory() as nearest_tmp_dir,
            tempfile.TemporaryDirectory() as bicubic_tmp_dir,
        ):
            # Update data directories
            config_bilinear.data_dir = bilinear_tmp_dir
            config_nearest.data_dir = nearest_tmp_dir
            config_bicubic.data_dir = bicubic_tmp_dir

            # Create temporary config files
            config_bilinear_path = Path(bilinear_tmp_dir) / "config_bilinear.yaml"
            config_nearest_path = Path(nearest_tmp_dir) / "config_nearest.yaml"
            config_bicubic_path = Path(bicubic_tmp_dir) / "config_bicubic.yaml"

            OmegaConf.save(config_bilinear, config_bilinear_path)
            OmegaConf.save(config_nearest, config_nearest_path)
            OmegaConf.save(config_bicubic, config_bicubic_path)

            # Download with bilinear resampling
            download_s1(config_bilinear_path)
            conf_bilinear = load(config_bilinear_path)
            bilinear_files = list(Path(conf_bilinear.data_dir).rglob("*.tif"))
            assert len(bilinear_files) == 1

            # Download with nearest resampling
            download_s1(config_nearest_path)
            conf_nearest = load(config_nearest_path)
            nearest_files = list(Path(conf_nearest.data_dir).rglob("*.tif"))
            assert len(nearest_files) == 1

            # Download with bicubic resampling
            download_s1(config_bicubic_path)
            conf_bicubic = load(config_bicubic_path)
            bicubic_files = list(Path(conf_bicubic.data_dir).rglob("*.tif"))
            assert len(bicubic_files) == 1

            # Read the downloaded files and compare their content
            with rio.open(bilinear_files[0]) as bilinear_ds:
                bilinear_data = bilinear_ds.read()

            with rio.open(nearest_files[0]) as nearest_ds:
                nearest_data = nearest_ds.read()

            with rio.open(bicubic_files[0]) as bicubic_ds:
                bicubic_data = bicubic_ds.read()

            # All outputs should be different from each other
            assert not np.array_equal(
                bilinear_data, nearest_data
            ), "Bilinear and nearest resampling produced identical outputs"
            assert not np.array_equal(
                bilinear_data, bicubic_data
            ), "Bilinear and bicubic resampling produced identical outputs"
            assert not np.array_equal(
                nearest_data, bicubic_data
            ), "Nearest and bicubic resampling produced identical outputs"

    def test_resolution(self, paris_config_path: Path):
        """Test that different resolution parameters produce images with different pixel sizes."""

        # Create two configs with different resolution values
        config_10m = OmegaConf.load(paris_config_path)
        config_30m = OmegaConf.load(paris_config_path)

        # Set different resolution values
        config_10m.satellite_default.resolution = 10
        config_30m.satellite_default.resolution = 30

        # Create separate temporary directories for each download
        with (
            tempfile.TemporaryDirectory() as res10_tmp_dir,
            tempfile.TemporaryDirectory() as res30_tmp_dir,
        ):
            # Update data directories
            config_10m.data_dir = res10_tmp_dir
            config_30m.data_dir = res30_tmp_dir

            # Create temporary config files
            config_10m_path = Path(res10_tmp_dir) / "config_10m.yaml"
            config_30m_path = Path(res30_tmp_dir) / "config_30m.yaml"

            OmegaConf.save(config_10m, config_10m_path)
            OmegaConf.save(config_30m, config_30m_path)

            # Download with 10m resolution
            download_s1(config_10m_path)
            conf_10m = load(config_10m_path)
            res10_files = list(Path(conf_10m.data_dir).rglob("*.tif"))
            assert len(res10_files) == 1

            # Download with 30m resolution
            download_s1(config_30m_path)
            conf_30m = load(config_30m_path)
            res30_files = list(Path(conf_30m.data_dir).rglob("*.tif"))
            assert len(res30_files) == 1

            # Read the downloaded files and compare their pixel sizes
            with rio.open(res10_files[0]) as res10_ds:
                res10_transform = res10_ds.transform
                res10_pixel_size_x = abs(res10_transform[0])  # Pixel width
                res10_pixel_size_y = abs(res10_transform[4])  # Pixel height

            with rio.open(res30_files[0]) as res30_ds:
                res30_transform = res30_ds.transform
                res30_pixel_size_x = abs(res30_transform[0])  # Pixel width
                res30_pixel_size_y = abs(res30_transform[4])  # Pixel height

            # The pixel sizes should be different (30m should be larger than 10m)
            assert res30_pixel_size_x > res10_pixel_size_x, (
                f"30m resolution pixel size ({res30_pixel_size_x}) should be"
                f"larger than 10m resolution pixel size ({res10_pixel_size_x})"
            )
            assert res30_pixel_size_y > res10_pixel_size_y, (
                f"30m resolution pixel size ({res30_pixel_size_y}) should be"
                f"larger than 10m resolution pixel size ({res10_pixel_size_y})"
            )
