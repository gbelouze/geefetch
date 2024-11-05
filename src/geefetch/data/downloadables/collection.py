"""This module provides downloading utility functions for Google Earth Engine's FeatureCollection,
similar to what `geedim` provides for Image and ImageCollection."""

import logging
import tempfile
import threading
from pathlib import Path
from typing import Any, List

import ee
import geopandas as gpd
import requests
from geobbox import GeoBoundingBox
from rasterio.crs import CRS

from ...utils.enums import Format
from ...utils.geopandas import merge_geojson
from ...utils.rasterio import WGS84
from .abc import DownloadableABC

log = logging.getLogger(__name__)

__all__: list[str] = []


class DownloadableGEECollection(DownloadableABC):
    lock = threading.Lock()

    def _get_download_url(
        self, collection: ee.FeatureCollection, format: Format
    ) -> tuple[requests.Response, str]:
        """Get tile download url and response."""
        with self.lock:
            url = collection.getDownloadURL(filetype=format.to_str())
            return requests.get(url, stream=True), url

    def __init__(self, collection: ee.FeatureCollection):
        self.collection = collection

    def download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: List[str],
        format: Format = Format.GEOJSON,
        split_recursion_depth: int = 0,
        **kwargs: Any,
    ) -> None:
        """Download a FeatureCollection in one go.
        It is up to the caller to make sure that the collection does not exceed Google Earth Engine compute limit.

        Parameters
        ----------
        collection : ee.FeatureCollection
            The collection to download.
        out : Path
            Path to the geojson file to download the collection to.
        bands : list[str]
            Properties of the collection to select for download.
        region : GeoBoundingBox
            The ROI.
        crs : CRS
            The CRS to use for the features' geometries.
        format : Format
            The desired filetype.
        """
        for key in kwargs.keys():
            if key not in ["scale", "progress", "max_tile_size"]:
                log.warn(f"Argument {key} is ignored.")

        if format == Format.GEOJSON and crs != WGS84:
            log.warn(f".geojson files must be in WGS84. Ignoring argument {crs=}.")
            crs = WGS84
        if format == Format.PARQUET:
            old_crs = crs
            crs = WGS84

        # get image download url and response
        collection = (
            self.collection.filterBounds(region.to_ee_geometry())
            .select(bands)
            .map(lambda feature: feature.transform(f"EPSG:{crs.to_epsg()}"))
        )
        response, url = self._get_download_url(
            collection, Format.GEOJSON if format == Format.PARQUET else format
        )

        def handle_error_response(response: requests.Response) -> None:
            resp_dict = response.json()
            if "error" in resp_dict and "message" in resp_dict["error"]:
                msg = resp_dict["error"]["message"]
                if (
                    msg
                    == "Unable to compute table: java.io.IOException: No space left on device"
                ):
                    if split_recursion_depth > 3:
                        log.error(
                            f"Attempted to split the download regions 3 times. Still getting error: {msg}. Aborting."
                        )
                        raise IOError(msg)
                    log.debug(
                        f"Caught GEE exception '[black]{msg}[/]' for tile {out}. "
                        "Attempting to split into smaller regions ({split_recursion_depth=})."
                    )
                    self.split_then_download(
                        out,
                        region,
                        crs,
                        bands,
                        format,
                        split_recursion_depth=split_recursion_depth + 1,
                        **kwargs,
                    )
                    return
                ex_msg = f"Error downloading tile: {msg}"
            else:
                ex_msg = str(response.json())
            raise IOError(ex_msg)

        if not response.ok:
            handle_error_response(response)

        if format == Format.PARQUET:
            with tempfile.NamedTemporaryFile(
                suffix=".geojson", delete=False
            ) as tmp_file:
                for data in response.iter_content(chunk_size=1024):
                    tmp_file.write(data)
                tmp_file.flush()
                gdf = gpd.read_file(tmp_file.name).to_crs(old_crs)
                gdf.reset_index(inplace=True, drop=True)
                gdf.to_parquet(out)
                Path(tmp_file.name).unlink()
                return
        with open(out, "wb") as geojsonfile:
            for data in response.iter_content(chunk_size=1024):
                geojsonfile.write(data)

    def split_then_download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: List[str],
        format: Format = Format.GEOJSON,
        split_recursion_depth: int = 0,
        **kwargs: Any,
    ) -> None:
        """Download a FeatureCollection by splitting the AOI then merging the results.

        Parameters
        ----------
        collection : ee.FeatureCollection
            The collection to download.
        out : Path
            Path to the geojson file to download the collection to.
        bands : list[str]
            Properties of the collection to select for download.
        region : GeoBoundingBox
            The ROI.
        crs : CRS
            The CRS to use for the features' geometries.
        format : Format
            The desired filetype.
        """
        match format:
            case Format.GEOJSON | Format.PARQUET:
                pass
            case _:
                raise NotImplementedError(
                    f"Splitting and merging is not supported for download format {format}."
                )
        center_northing, center_easting = region.center
        northings = [region.bottom, center_northing, region.top]
        eastings = [region.left, center_easting, region.right]
        regions = [
            GeoBoundingBox(left, bottom, right, top, crs=region.crs)
            for left, right in zip(eastings[:-1], eastings[1:])
            for bottom, top in zip(northings[:-1], northings[1:])
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_paths = []
            for i, region in enumerate(regions):
                tmp_path = Path(tmp_dir) / f"{i}.{format.to_str()}"
                tmp_paths.append(tmp_path)
                self.download(
                    tmp_path,
                    region,
                    crs,
                    bands,
                    Format.GEOJSON,
                    split_recursion_depth,
                    **kwargs,
                )
                log.debug(f"Downloaded [{i+1}/4] split for {out}.")
            gdf = merge_geojson(tmp_paths)
        if format == Format.PARQUET:
            gdf.to_parquet(out)
        else:
            gdf.to_file(out)
