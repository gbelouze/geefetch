"""This module provides downloading utility functions for Google Earth Engine's FeatureCollection,
similar to what `geedim` provides for Image and ImageCollection."""

import logging
import tempfile
import threading
from pathlib import Path
from typing import Any

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

    def __init__(self, collection: ee.FeatureCollection):
        self.collection = collection

    def _get_download_url(
        self, collection: ee.FeatureCollection, format: Format
    ) -> tuple[requests.Response, str]:
        """Get tile download url and response."""
        with self.lock:
            url = collection.getDownloadURL(filetype=format.to_str())
            return requests.get(url, stream=True), url

    def download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: list[str],
        format: Format = Format.GEOJSON,
        **kwargs: Any,
    ) -> None:
        """Download a FeatureCollection in one go.
        It is up to the caller to make sure that the collection does not exceed
        Google Earth Engine compute limit.

        Parameters
        ----------
        out : Path
            Path to the geojson file to download the collection to.
        region : GeoBoundingBox
            The ROI.
        crs : CRS
            The CRS to use for the features' geometries.
        bands : list[str]
            Properties of the collection to select for download.
        format : Format
            The desired filetype.
        **kwargs : Any
            Accepted but ignored additional arguments.
        """
        for key in kwargs:
            if key not in ["scale", "progress", "max_tile_size"]:
                log.warning(f"Argument {key} is ignored.")
        return self._recursively_download(out, region, crs, bands, format)

    def _recursively_download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: list[str],
        format: Format = Format.GEOJSON,
        _split_recursion_depth: int = 0,
        **kwargs: Any,
    ) -> None:
        for key in kwargs:
            if key not in ["scale", "progress", "max_tile_size"]:
                log.warning(f"Argument {key} is ignored.")

        if format == Format.GEOJSON and crs != WGS84:
            log.warning(f".geojson files must be in WGS84. Ignoring argument {crs=}.")
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
        response, _ = self._get_download_url(
            collection, Format.GEOJSON if format == Format.PARQUET else format
        )

        def handle_error_response(response: requests.Response) -> None:
            resp_dict = response.json()
            if "error" in resp_dict and "message" in resp_dict["error"]:
                msg = resp_dict["error"]["message"]
                if msg == "Unable to compute table: java.io.IOException: No space left on device":
                    if _split_recursion_depth > 3:
                        log.error(
                            "Attempted to split the download regions 3 times. "
                            f"Still getting error: {msg}. Aborting."
                        )
                        raise OSError(msg)
                    log.debug(
                        f"Caught GEE exception '[black]{msg}[/]' for tile {out}. "
                        f"Attempting to split into smaller regions ({_split_recursion_depth=})."
                    )
                    self._split_then_download(
                        out,
                        region,
                        crs,
                        bands,
                        format,
                        _split_recursion_depth=_split_recursion_depth + 1,
                        **kwargs,
                    )
                    return
                ex_msg = f"Error downloading tile: {msg}"
            else:
                ex_msg = str(response.json())
            raise OSError(ex_msg)

        if not response.ok:
            handle_error_response(response)
            return

        if format == Format.PARQUET:
            with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tmp_file:
                for data in response.iter_content(chunk_size=1024):
                    tmp_file.write(data)
                tmp_file.flush()
                gdf = gpd.read_file(tmp_file.name).to_crs(old_crs)
                Path(tmp_file.name).unlink()
            gdf.reset_index(inplace=True, drop=True)
            gdf.to_parquet(out)
            return
        with out.open("wb") as geojsonfile:
            for data in response.iter_content(chunk_size=1024):
                geojsonfile.write(data)

    def _split_then_download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: list[str],
        format: Format = Format.GEOJSON,
        _split_recursion_depth: int = 0,
        **kwargs: Any,
    ) -> None:
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
            for left, right in zip(eastings[:-1], eastings[1:], strict=True)
            for bottom, top in zip(northings[:-1], northings[1:], strict=True)
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_paths = []
            for i, region in enumerate(regions):
                tmp_path = Path(tmp_dir) / f"{i}.{format.to_str()}"
                tmp_paths.append(tmp_path)
                self._recursively_download(
                    tmp_path,
                    region,
                    crs,
                    bands,
                    Format.GEOJSON,
                    _split_recursion_depth,
                    **kwargs,
                )
                log.debug(f"Downloaded [{i + 1}/4] split for {out}.")
            gdf = merge_geojson(tmp_paths)
        if format == Format.PARQUET:
            gdf.to_parquet(out)
        else:
            gdf.to_file(out)
