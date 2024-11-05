"""
[LEGACY CODE]
This module provides downloading utility functions for Google Earth Engine's Image,
similar to what `geedim` provides for Image and ImageCollection.
"""

import logging
import threading
from pathlib import Path
from typing import Any, List

import ee
import requests
from geobbox import GeoBoundingBox
from rasterio.crs import CRS

from .abc import DownloadableABC

log = logging.getLogger(__name__)

__all__: list[str] = []


class DownloadableGEEImage(DownloadableABC):
    lock = threading.Lock()

    def _get_download_url(
        self,
        image: ee.Image,
        bands: List[str],
        region: GeoBoundingBox,
        crs: str,
    ) -> tuple[requests.Response, str]:
        """Get tile download url and response."""
        with self.lock:
            url = image.getDownloadURL(
                dict(
                    format="GEO_TIFF",
                    region=region.to_ee_geometry(),
                    crs=crs,
                    bands=bands,
                )
            )
            return requests.get(url, stream=True), url

    def __init__(self, image: ee.Image):
        self.image = image

    def download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: List[str],
        **kwargs: Any,
    ) -> None:
        """Download a GEE Image in one go.
        It is up to the caller to make sure that the image does not exceed Google Earth Engine compute limit.

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
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")

        gee_crs = f"EPSG:{crs.to_epsg()}"

        # get image download url and response
        image = self.image
        response, url = self._get_download_url(image, bands, region, gee_crs)

        download_size = int(response.headers.get("content-length", 0))

        if download_size == 0 or not response.ok:
            resp_dict = response.json()
            if "error" in resp_dict and "message" in resp_dict["error"]:
                msg = resp_dict["error"]["message"]
                ex_msg = f"Error downloading tile: {msg}"
            else:
                ex_msg = str(response.json())
            raise IOError(ex_msg)

        with open(out, "wb") as geojsonfile:
            for data in response.iter_content(chunk_size=1024):
                geojsonfile.write(data)
