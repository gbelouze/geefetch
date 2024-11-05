"""Utilities for working with different system of coordinates."""

import logging
import sys

import ee
import geobbox
import rasterio as rio
import rasterio.warp as warp
from geobbox import GeoBoundingBox
from rasterio.crs import CRS

log = logging.getLogger(__name__)

if (sys.version_info.major, sys.version_info.minor) < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

__all__ = ["UTM", "WGS84", "BoundingBox"]


Coordinate: TypeAlias = tuple[float, float]


WGS84 = CRS.from_epsg(4326)


class UTM(geobbox.UTM):
    """
    .. deprecated:: 0.4.0
          `UTM` will be removed in GeeFetch 0.5.0, it is replaced by
          `geobbox.UTM` coming from the standalone package `geobbox`.

    """

    def __init__(self, *args, **kwargs):
        log.warn(
            "geefetch.coords.UTM is decrecated and will be removed in GeeFetch 0.5.0. Use `geobbox.UTM` instead."
        )
        super().__init__(*args, **kwargs)


class BoundingBox(GeoBoundingBox):
    """
    .. deprecated:: 0.4.0
          `BoundingBox` will be removed in GeeFetch 0.5.0, it is replaced by
          `geobbox.GeoBoundingBox` coming from the standalone package `geobbox`.

    """

    def __init__(self, *args, **kwargs):
        log.warn(
            "geefetch.coords.UTM is decrecated and will be removed in GeeFetch 0.5.0. Use `geobbox.UTM` instead."
        )
        super().__init__(*args, **kwargs)


def close_to_utm_border(lat: float, lon: float, delta: float = 1.0) -> bool:
    """Check if the point at coordinate (lat, lon) is delta-close to a UTM border.

    .. deprecated:: 0.4.0
          `close_to_utm_border` will be removed in GeeFetch 0.5.0.
    """
    log.warn(
        "`geefetch.coords.close_to_utm_border` is decrecated and will be removed in GeeFetch 0.5.0."
    )
    return not (delta < lon % 6 < 6 - delta)


def get_center_tif(ds: rio._base.DatasetBase) -> Coordinate:
    """Compute the center of a tif image in WGS84 CRS.

    Parameters
    ----------
    ds : rio._base.DatasetBase
        A rio dataset representing a tif image.

    Returns
    -------
    lat, lon : Coordinate
        Latitude and longitude of the center of `ds`.

    Example
    -------
    ds = rio.open("example.tif")
    m = folium.Map(location=getCenterTif(ds))

    .. deprecated:: 0.4.0
          `get_center_tif` will be removed in GeeFetch 0.5.0.

    """
    log.warn(
        "`geefetch.coords.get_center_tif` is decrecated and will be removed in GeeFetch 0.5.0."
    )
    x, y = ds.xy(ds.height // 2, ds.width // 2)
    lon, lat = warp.transform(ds.crs, WGS84, [x], [y])
    return lat[0], lon[0]


def get_shape_image(image: ee.Image) -> tuple[int, int]:
    """Compute the shape of a GEE image in (width, height) format.

    Parameters
    ----------
    image : ee.Image

    Returns
    -------
    w, h : tuple[int, int]

    .. deprecated:: 0.4.0
          `get_shape_image` will be removed in GeeFetch 0.5.0.

    """
    log.warn(
        "`geefetch.coords.get_shape_image` is decrecated and will be removed in GeeFetch 0.5.0."
    )
    shape: tuple[int, int] = image.getInfo()["bands"][0]["dimensions"]  # type: ignore[index]
    return shape


def get_bounding_box_tif(ds: rio._base.DatasetBase) -> tuple[Coordinate, Coordinate]:
    """Compute the bounding box of a tif image in WGS84 CRS.

    Parameters
    ----------
    ds : rio._base.DatasetBase
        A rio dataset representing a tif image.

    Returns
    -------
    (lat_min, lon_min), (lat_max, lon_max) : Coordinate, Coordinate
        Coordinates of the top right and bottom left box corners.

    .. deprecated:: 0.4.0
          `get_bounding_box_tif` will be removed in GeeFetch 0.5.0.

    """
    log.warn(
        "`geefetch.coords.get_bounding_box_tif` is decrecated and will be removed in GeeFetch 0.5.0."
    )
    return BoundingBox.from_rio(ds.bounds, crs=ds.crs).transform(WGS84).to_latlon()
