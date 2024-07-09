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
from rasterio.crs import CRS

from ...coords import WGS84
from ...enums import Format
from .abc import DownloadableABC

log = logging.getLogger(__name__)

__all__ = []


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
        region: ee.Geometry,
        crs: CRS,
        bands: List[str],
        format: Format = Format.GEOJSON,
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
        region : ee.Geometry
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
            self.collection.filterBounds(region)
            .select(bands)
            .map(lambda feature: feature.transform(f"EPSG:{crs.to_epsg()}"))
        )
        response, url = self._get_download_url(
            collection, Format.GEOJSON if format == Format.PARQUET else format
        )

        if not response.ok:
            resp_dict = response.json()
            if "error" in resp_dict and "message" in resp_dict["error"]:
                msg = resp_dict["error"]["message"]
                ex_msg = f"Error downloading tile: {msg}"
            else:
                ex_msg = str(response.json())
            raise IOError(ex_msg)

        if format == Format.PARQUET:
            with tempfile.NamedTemporaryFile(suffix=".geojson") as tmp_file:
                for data in response.iter_content(chunk_size=1024):
                    tmp_file.write(data)
                tmp_file.flush()
                gdf = gpd.read_file(tmp_file.name).to_crs(old_crs)
                gdf.to_parquet(out)
                return
        with open(out, "wb") as geojsonfile:
            for data in response.iter_content(chunk_size=1024):
                geojsonfile.write(data)
