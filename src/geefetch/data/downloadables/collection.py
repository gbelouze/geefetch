"""This module provides downloading utility functions for Google Earth Engine's FeatureCollection,
similar to what `geedim` provides for Image and ImageCollection."""

import logging
import tempfile
from concurrent.futures import (
    Executor,
    ThreadPoolExecutor,
    as_completed,
)
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import geopandas as gpd
import requests
from ee.featurecollection import FeatureCollection
from geobbox import GeoBoundingBox
from rasterio import CRS
from rich.progress import Progress

from geefetch.utils.multiprocessing import SequentialExecutor
from geefetch.utils.progress import geefetch_debug
from geefetch.utils.progress_multiprocessing import add_task_finally_remove

from ...utils.enums import Format
from ...utils.geopandas import merge_geojson, merge_parquet
from ...utils.rasterio import WGS84
from ...utils.split import approximate_split
from .abc import DownloadableABC

log = logging.getLogger(__name__)

__all__: list[str] = []


class DownloadError(Exception):
    pass


def _tile_name(tile: GeoBoundingBox) -> str:
    return f"{int(tile.left):_}_{int(tile.right):_}_{int(tile.bottom):_}_{int(tile.top):_}"


class DownloadableGEECollection(DownloadableABC):
    """Downloads feature collections from Google Earth Engine.

    This class handles downloading Earth Engine FeatureCollections to local files
    in either GeoJSON or Parquet format. It implements automatic splitting of large
    collection requests to handle Earth Engine compute limits, with recursive retries
    when a download fails.

    Parameters
    ----------
    collection : FeatureCollection
        The Earth Engine FeatureCollection to download.
    """

    def __init__(self, collection: FeatureCollection):
        self.collection = collection

    def _get_download_url(
        self, collection: FeatureCollection, format: Format
    ) -> tuple[requests.Response, str]:
        """Get tile download url and response."""
        url = collection.getDownloadURL(filetype=format.to_str())
        return requests.get(url, stream=True), url

    def download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: list[str],
        format: Format = Format.GEOJSON,
        progress: Progress | None = None,
        **kwargs: Any,
    ) -> None:
        """Download a FeatureCollection in one go.
        It is up to the caller to make sure that the collection does not exceed
        Google Earth Engine compute limit.

        Parameters
        ----------
        out : Path
            Path to the file to download the collection to.
        region : GeoBoundingBox
            The Region Of Interest.
        crs : CRS
            The CRS to use for the features' geometries.
        bands : list[str]
            Properties of the collection to select for download.
        format : Format
            The desired filetype.
        progress : Progress | None
            An optional rich progress object to track download. Defaults to None.
        **kwargs : Any
            Accepted but ignored additional arguments.
        """
        for key in kwargs:
            if key not in ["scale", "progress", "max_tile_size"]:
                log.warning(f"Argument {key} is ignored.")

        old_crs = crs
        if format == Format.GEOJSON and crs != WGS84:
            log.warning(f".geojson files must be in WGS84. Ignoring argument {crs=}.")
            crs = WGS84
        elif format == Format.PARQUET:
            # we have to download as GEOJSON and convert as parquet later
            crs = WGS84

        # don't use too any workers or we reach a number of requests per minute GEE quota limit
        max_workers = 25

        downloaded_paths = []
        if geefetch_debug():
            max_workers = 1
            executor_cls: type[Executor] = SequentialExecutor
        else:
            executor_cls = ThreadPoolExecutor
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            executor_cls(max_workers=max_workers) as executor,
            ExitStack() as stack,
        ):
            split_tiles = list(
                approximate_split(
                    region,
                    minimal_size=10_000
                    if region.crs.is_projected
                    else 0.1,  # approximately 10km in m or in deg
                )
            )

            n_tiles_download = len(split_tiles)
            if n_tiles_download > 1_000:
                raise ValueError(f"Region is split in too many tiles {n_tiles_download=}.")

            task = None
            if progress is not None:
                task = stack.enter_context(
                    add_task_finally_remove(
                        progress, f"[magenta]Downloading {out.name}[/]", total=n_tiles_download
                    )
                )

            futures = []
            for tile in split_tiles:
                tile_path = Path(tmpdir) / f"{_tile_name(tile)}{out.suffix}"
                future = executor.submit(self._download, tile_path, tile, crs, bands, format)
                futures.append(future)

            recursive_depth = 0
            while len(futures) > 0:
                new_futures = []
                for completed in as_completed(futures):
                    response, tile_path, tile = completed.result()
                    if response is None:
                        downloaded_paths.append(tile_path)
                        if progress is not None and task is not None:
                            progress.advance(task)
                        continue
                    resp_dict = response.json()
                    if not (
                        "error" in resp_dict
                        and "message" in resp_dict["error"]
                        and resp_dict["error"]["message"]
                        == "Unable to compute table: java.io.IOException: No space left on device"
                    ):
                        raise DownloadError(str(response.json()))
                    msg = resp_dict["error"]["message"]
                    if (
                        tile.crs.is_projected
                        and tile.area < 2_000**2 / 16
                        or not tile.crs.is_projected
                        and tile.area < 0.02**2 / 16
                    ):
                        log.error(
                            "Attempted to split the download regions to less than 25 km². "
                            "Still getting error. Aborting."
                        )
                        raise DownloadError(msg)

                    split_width = min((tile.right - tile.left) / 2, (tile.top - tile.bottom) / 2)
                    split_tiles = list(approximate_split(tile, split_width))

                    log.debug(
                        f"Caught GEE exception '[black]{msg}[/]' for tile {out}. "
                        f"Attempting to split into smaller regions (side length = {split_width})."
                    )

                    for tile in split_tiles:
                        tile_path = Path(tmpdir) / f"{_tile_name(tile)}{out.suffix}"
                        future = executor.submit(
                            self._download, tile_path, tile, crs, bands, format
                        )
                        new_futures.append(future)
                futures = new_futures
                recursive_depth += 1
                if recursive_depth > 3:
                    raise DownloadError(
                        "Maximum recursive depth for collection download reached."
                        "Try with a smaller AOI or check satellite data."
                    )

                if len(futures) > 0:
                    log.debug(
                        f"Queuing {len(futures)} additional downloads on smaller tiles "
                        f"({recursive_depth=})."
                    )
                    n_tiles_download += len(futures)
                    if progress is not None and task is not None:
                        progress.update(task, total=n_tiles_download)

            if progress is not None and task is not None:
                progress.update(task, visible=False)

            if format == Format.PARQUET:
                gdf = merge_parquet(downloaded_paths)
            elif format == Format.GEOJSON:
                gdf = merge_geojson(downloaded_paths)
            else:
                raise ValueError(f"Don't how to merge files with format {format}")

        tmp_out = out.with_suffix(f".tmp{out.suffix}")
        tmp_out.unlink(missing_ok=True)

        if len(gdf) == 0:
            log.warning(f"No data found for {out}. Skipping.")
            return

        if format == Format.PARQUET:
            gdf.reset_index(inplace=True, drop=True)
            gdf.to_crs(old_crs).to_parquet(tmp_out)
        else:
            gdf.to_file(tmp_out)

        tmp_out.replace(out)

    def _download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: list[str],
        format: Format = Format.GEOJSON,
        _split_recursion_depth: int = 0,
    ) -> tuple[requests.Response | None, Path, GeoBoundingBox]:
        # get image download url and response
        collection = (
            self.collection.filterBounds(region.to_ee_geometry())
            .select(bands)
            .map(lambda feature: feature.transform(f"EPSG:{crs.to_epsg()}"))
        )
        response, _ = self._get_download_url(
            collection, Format.GEOJSON if format == Format.PARQUET else format
        )

        if not response.ok:
            return response, out, region

        if format == Format.PARQUET:
            with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tmp_file:
                for data in response.iter_content(chunk_size=1024):
                    tmp_file.write(data)
                tmp_file.flush()
                gdf = gpd.read_file(tmp_file.name)
                assert isinstance(gdf, gpd.GeoDataFrame)
                Path(tmp_file.name).unlink()
            gdf.reset_index(inplace=True, drop=True)
            gdf.to_parquet(out)
            return None, out, region
        with out.open("wb") as geojsonfile:
            for data in response.iter_content(chunk_size=1024):
                geojsonfile.write(data)
        return None, out, region
