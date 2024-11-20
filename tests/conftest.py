import logging
import os
from pathlib import Path

import pytest
from omegaconf import DictConfig, OmegaConf

from geefetch.cli.omegaconfig import GeefetchConfig, load
from geefetch.utils.enums import CompositeMethod

TESTS_DIR = Path(__file__).parent
GEE_PROJECT_ID_ENV_NAME = "GEEFETCH_GEE_PROJECT_ID"


@pytest.fixture
def raw_paris_config() -> DictConfig:
    return OmegaConf.load(TESTS_DIR / "data" / "paris_config.yaml")


@pytest.fixture(scope="session")
def gee_project_id() -> str:
    match os.getenv(GEE_PROJECT_ID_ENV_NAME):
        case None:
            pytest.fail(
                f"Did not find {GEE_PROJECT_ID_ENV_NAME} in the environment. "
                "Cannot query Google Earth Engine."
            )
        case _ as project_id:
            assert isinstance(project_id, str)
            return project_id


@pytest.fixture
def paris_config_path(raw_paris_config: DictConfig, tmp_path: Path, gee_project_id: str) -> Path:
    raw_paris_config.data_dir = str(tmp_path)
    raw_paris_config.satellite_default.gee.ee_project_id = gee_project_id

    conf_path = tmp_path / "config.yaml"
    conf_path.write_text(OmegaConf.to_yaml(raw_paris_config))
    return conf_path


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
def paris_config(paris_config_path: Path) -> GeefetchConfig:
    return load(paris_config_path)


@pytest.fixture
def paris_timeseries_config(paris_config_path: Path) -> GeefetchConfig:
    config = load(paris_config_path)
    config.satellite_default.composite_method = CompositeMethod.TIMESERIES
    return config


# ----
# Add pytest.mark.slow marker
# See also https://stackoverflow.com/a/47567535/24033350


def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", help="Don't skip tests marked with @slow")


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("Need flag '--run-slow' to run this test.")


# ---
# Configure logging


def pytest_configure(config):
    """Disable the loggers."""
    for logger_name in [
        "google",
        "urllib3",
        "googleapiclient",
        "rasterio",
        "geedim",
        "patched_geedim",
    ]:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
