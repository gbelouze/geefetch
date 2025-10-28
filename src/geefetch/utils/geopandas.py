import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

from ..utils.rasterio import WGS84

log = logging.getLogger(__name__)


def merge_parquet(paths: list[Path]) -> gpd.GeoDataFrame:
    log.debug("Merging .parquet files")
    gdfs = []
    for path in paths:
        gdfs.append(gpd.read_parquet(path))
    gdfs = [gdf for gdf in gdfs if len(gdf) > 0]

    crss = set(gdf.crs for gdf in gdfs)
    if len(crss) > 1:
        common_crs = WGS84
    elif len(crss) == 1:
        common_crs = crss.pop()
    else:
        log.error("No .parquet files found.")
        return gpd.GeoDataFrame([], geometry=[])

    for gdf in gdfs:
        gdf.to_crs(common_crs, inplace=True)

        # FutureWarning workaround : https://github.com/pandas-dev/pandas/issues/55928
        gdf.dropna(axis=1, how="all", inplace=True)

    return gpd.GeoDataFrame(pd.concat(gdfs))


def merge_geojson(paths: list[Path]) -> gpd.GeoDataFrame:
    log.debug("Merging .geojson files")
    gdfs = []
    for path in paths:
        gdfs.append(gpd.read_file(path))
    gdfs = [gdf for gdf in gdfs if len(gdf) > 0]

    crss = set(gdf.crs for gdf in gdfs)
    if len(crss) > 1:
        common_crs = WGS84
    elif len(crss) == 1:
        common_crs = crss.pop()
    else:
        raise ValueError("No .parquet files found.")

    for gdf in gdfs:
        gdf.to_crs(common_crs, inplace=True)

        # FutureWarning workaround : https://github.com/pandas-dev/pandas/issues/55928
        gdf.dropna(axis=1, how="all", inplace=True)

    return gpd.GeoDataFrame(pd.concat(gdfs))
