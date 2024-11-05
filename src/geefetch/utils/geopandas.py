import logging
from pathlib import Path
from typing import List

import geopandas as gpd
import pandas as pd

from ..utils.rasterio import WGS84

log = logging.getLogger(__file__)


def merge_parquet(paths: List[Path]) -> gpd.GeoDataFrame:
    log.debug("Merging .parquet files")
    gdfs = []
    for path in paths:
        gdfs.append(gpd.read_parquet(path))

    crss = set(gdf.crs for gdf in gdfs)
    if len(crss) > 1:
        common_crs = WGS84
    elif len(crss) == 1:
        common_crs = crss.pop()
    else:
        raise ValueError("No .parquet files found.")
    gdfs = [gdf.to_crs(common_crs) for gdf in gdfs]

    return gpd.GeoDataFrame(pd.concat(gdfs))


def merge_geojson(paths: List[Path]) -> gpd.GeoDataFrame:
    log.debug("Merging .geojson files")
    gdfs = []
    for path in paths:
        gdfs.append(gpd.read_file(path))

    crss = set(gdf.crs for gdf in gdfs)
    if len(crss) > 1:
        common_crs = WGS84
    elif len(crss) == 1:
        common_crs = crss.pop()
    else:
        raise ValueError("No .parquet files found.")
    gdfs = [gdf.to_crs(common_crs) for gdf in gdfs]

    return gpd.GeoDataFrame(pd.concat(gdfs))
