"""
This subpackage is designed to facilitate the downloading of satellite data from Google Earth Engine (GEE).

It provides abstract base classes for defining download interfaces and satellite metadata,
as well as concrete implementations with sane defaults for some Google Earth Engine datasets.
It is easily extensible to support other GEE datasets.

It also provides functions to download composite or raw time series data.
"""

from . import downloadables, get, process, satellites

__all__ = ["downloadables", "get", "process", "satellites"]
