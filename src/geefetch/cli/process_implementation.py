import logging
from pathlib import Path

from geefetch.data import satellites
from geefetch.data.process import clean as dataset_clean
from geefetch.data.process import (
    gedi_is_clean,
    merge_geojson,
    merge_parquet,
    tif_is_clean,
)
from geefetch.data.tiler import TileTracker

from .omegaconfig import load

log = logging.getLogger(__name__)


def clean(config_path: Path, s1: bool, s2: bool, gedi: bool, num_threads: int) -> None:
    """Remove corrupted .tif files."""
    conf = load(config_path)
    if s1:
        tracker = TileTracker(
            satellites.S1(), conf.data_dir, filter=lambda x: x.suffix == ".tif"
        )
        log.info(f"Cleaning {tracker}")
        dataset_clean(tracker, tif_is_clean, max_threads=num_threads)
    if s2:
        tracker = TileTracker(
            satellites.S2(), conf.data_dir, filter=lambda x: x.suffix == ".tif"
        )
        log.info(f"Cleaning {tracker}")
        dataset_clean(tracker, tif_is_clean, max_threads=num_threads)
    if gedi:
        tracker = TileTracker(
            satellites.GEDIraster(), conf.data_dir, filter=lambda x: x.suffix == ".tif"
        )
        log.info(f"Cleaning {tracker}")
        dataset_clean(tracker, gedi_is_clean, max_threads=num_threads)


def merge_parquet_dataset(config_path: Path) -> None:
    """Merge Gedi vector parquet files into a single one."""
    conf = load(config_path)
    tracker = TileTracker(
        satellites.GEDIvector(), conf.data_dir, filter=lambda x: x.suffix == ".parquet"
    )
    merge_parquet(tracker)


def merge_geojson_dataset(config_path: Path) -> None:
    """Merge Gedi vector geojson files into a single one."""
    conf = load(config_path)
    tracker = TileTracker(
        satellites.GEDIvector(), conf.data_dir, filter=lambda x: x.suffix == ".geojson"
    )
    merge_geojson(tracker)
