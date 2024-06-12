import logging
from pathlib import Path

from ..data import satellites
from ..data.process import clean as dataset_clean
from ..data.process import gedi_is_clean, merge_geojson, tif_is_clean
from ..data.tiler import TileTracker
from .omegaconfig import load

log = logging.getLogger(__name__)


def clean(config_path: Path, s1: bool, s2: bool, gedi: bool, num_threads: int) -> None:
    """Remove corrupted .tif files."""
    conf = load(config_path)
    if s1:
        tracker = TileTracker(
            satellites.s1, conf.data_dir, filter=lambda x: x.suffix == ".tif"
        )
        log.info(f"Cleaning {tracker}")
        dataset_clean(tracker, tif_is_clean, max_threads=num_threads)
    if s2:
        tracker = TileTracker(
            satellites.s2, conf.data_dir, filter=lambda x: x.suffix == ".tif"
        )
        log.info(f"Cleaning {tracker}")
        dataset_clean(tracker, tif_is_clean, max_threads=num_threads)
    if gedi:
        tracker = TileTracker(
            satellites.gedi_raster, conf.data_dir, filter=lambda x: x.suffix == ".tif"
        )
        log.info(f"Cleaning {tracker}")
        dataset_clean(tracker, gedi_is_clean, max_threads=num_threads)


def merge_geojson_dataset(config_path: Path) -> None:
    """Merge Gedi vector geojson files into a single one."""
    conf = load(config_path)
    tracker = TileTracker(
        satellites.gedi_vector, conf.data_dir, filter=lambda x: x.suffix == ".geojson"
    )
    merge_geojson(tracker)
