"""This module contains data post-processing functions."""

import json
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio as rio
from rasterio.windows import Window

from ..utils.geopandas import merge_geojson, merge_parquet
from .tiler import TileTracker

log = logging.getLogger(__name__)

__all__ = [
    "geofile_is_clean",
    "tif_is_clean",
    "gedi_is_clean",
    "vector_is_clean",
    "merge_geojson",
    "merge_parquet",
]


def tif_is_not_corrupted(path: Path) -> bool:
    """Check that a 'tif' file is not corrupted, i.e. can be open with rasterio."""
    try:
        with rio.open(path) as x:
            x.read(1, window=Window(0, 0, 1, 1))
    except rio.RasterioIOError:
        return False
    return True


def tif_is_clean(path: Path) -> bool:
    """Check that a 'tif' file is valid and not full of NODATA."""
    try:
        with rio.open(path) as x:
            if x.read_masks().sum() / x.read().size < 0.9:
                # less than 10% valid data
                return False
    except rio.RasterioIOError:
        return False
    return True


def gedi_is_clean(path: Path) -> bool:
    """Check if the rasterized gedi at location `path` is not full of NODATA."""
    try:
        with rio.open(path) as x:
            if x.read_masks().sum() / x.read().size < 0.005:
                # less than 0.5% valid data
                return False
    except rio.RasterioIOError:
        return False
    return True


def vector_is_clean(fpath: Path) -> bool:
    """Check if the geojson file at location `path` is not empty."""
    try:
        match fpath.suffix:
            case ".geojson":
                x = json.loads(fpath.read_text())
                return "features" in x and len(x["features"]) > 0
            case ".csv":
                return len(pd.read_csv(fpath, header=0)) > 0
            case ".parquet":
                return len(gpd.read_parquet(fpath)) > 0
            case _ as suffix:
                log.warning(f"Don't know how to check {suffix} file {fpath}")
                return True
    except pd.errors.EmptyDataError:
        return False


def geofile_is_clean(fpath: Path) -> bool:
    """Check if the geofile at location `path` is not corrupted."""
    match fpath.suffix:
        case ".tif" | ".vrt":
            return tif_is_not_corrupted(fpath)
        case ".geojson" | ".csv" | ".parquet":
            return vector_is_clean(fpath)
        case _ as suffix:
            log.warning(f"Don't know how to check {suffix} file {fpath}")
            return True


def merge_tracked_parquet(tracker: TileTracker) -> None:
    merged_path = tracker.root / "merged.parquet"
    if merged_path.exists():
        log.error(f"A merged file {merged_path} already exists. Aborting...")
        return
    paths = [path for path in tracker]
    if len(paths) == 0:
        log.error(f"Found no file to merge in {tracker.root}.")
        return
    merged_gpd = merge_parquet(paths)
    merged_gpd.reset_index(inplace=True, drop=True)
    merged_gpd.to_parquet(merged_path)
    log.info(f"Merged parquet dataset into {merged_path}")


def merge_tracked_geojson(tracker: TileTracker) -> None:
    merged_path = tracker.root / "merged.geojson"
    if merged_path.exists():
        log.error(f"A merged file {merged_path} already exists. Aborting...")
        return
    paths = [path for path in tracker]
    if len(paths) == 0:
        log.error(f"Found no file to merge in {tracker.root}.")
        return
    merged = merge_geojson(paths)
    merged_path.write_text(json.dumps(merged))
    log.info(f"Merged geojson dataset into {merged_path}")
