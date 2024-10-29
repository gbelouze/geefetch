"""This module contains data post-processing functions."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import geopandas as gpd
import pandas as pd
import rasterio as rio

from ..utils.geopandas import merge_geojson, merge_parquet
from ..utils.progress import default_bar
from .tiler import TileTracker

log = logging.getLogger(__name__)

__all__ = [
    "tif_is_clean",
    "gedi_is_clean",
    "vector_is_clean",
    "merge_geojson",
    "merge_parquet",
    "clean",
]


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


def vector_is_clean(path: Path) -> bool:
    """Check if the geojson file at location `path` is not empty."""
    try:
        match path.suffix:
            case ".geojson":
                with open(path, "r") as fp:
                    x = json.load(fp)
                    return "features" in x and len(x["features"]) > 0
            case ".csv":
                return len(pd.read_csv(path, header=0)) > 0
            case ".parquet":
                return len(gpd.read_parquet(path)) > 0
            case _ as suffix:
                log.warn(f"Don't know how to check {suffix} file {path}")
                return True
    except pd.errors.EmptyDataError:
        return False


def clean(
    tracker: TileTracker, is_clean: Callable[[Path], bool], max_threads: int = 8
) -> int:
    """Remove ill-formed and empty data files.

    Parameters
    ----------
    is_clean: Callable[[Path, Tile], bool]
        The filtering function, called on every registered tile to determined
        whether it should be kept.
    max_threads: int
        Number of threads to use for processing the tiler.

    Returns
    -------
    int
        The number of removed files.
    """
    remove_count = 0
    paths = [path for path in iter(tracker)]
    with default_bar() as progress:
        task = progress.add_task("Finding corrupted tiles...", total=len(paths))
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(is_clean, path) for path in paths]
            log.debug("Futures submitted.")
            try:
                while (n_finished := sum([future.done() for future in futures])) < len(
                    futures
                ):
                    progress.update(task, completed=n_finished, total=len(futures))
            except KeyboardInterrupt:
                log.error(
                    "Keyboard interrupt while cleaning data. "
                    "[red]Please wait[/] while current processes finish (this may take up to a few minutes)."
                )
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            except Exception as e:
                log.error(f"Exception while cleaning tiler: {str(e)}\nCancelling...")
                executor.shutdown(wait=True, cancel_futures=True)
                raise e
        is_clean_results = [future.result() for future in as_completed(futures)]

    with default_bar() as progress:
        for path, tile_is_clean in zip(paths, is_clean_results):
            if not tile_is_clean:
                path.unlink()
                log.debug(f"Ill formed or empty .tif file [cyan]{path}[/]. Removed.")
                remove_count += 1
    log.info(
        f"Removed {remove_count} ill formed or empty.tif files in [cyan]{tracker.root}[/]"
    )
    return remove_count


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
    with open(merged_path, "w") as f:
        json.dump(merged, f)
        log.info(f"Merged geojson dataset into {merged_path}")
