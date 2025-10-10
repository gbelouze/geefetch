import logging
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from omegaconf import DictConfig, ListConfig, OmegaConf

TESTS_DIR = Path(__file__).parent
GEE_PROJECT_ID_ENV_NAME = "GEEFETCH_GEE_PROJECT_ID"
load_dotenv()


@pytest.fixture
def raw_paris_config() -> DictConfig | ListConfig:
    return OmegaConf.load(TESTS_DIR / "data" / "paris_config.yaml")


@pytest.fixture(scope="session")
def gee_project_id() -> str:
    match os.getenv(GEE_PROJECT_ID_ENV_NAME):
        case None:
            pytest.fail(
                f"Did not find {GEE_PROJECT_ID_ENV_NAME} in the environment. "
                "Cannot query Google Earth Engine."
            )
            raise RuntimeError
        case _ as project_id:
            assert isinstance(project_id, str)
            return project_id


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
