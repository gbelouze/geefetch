import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_object_dtype

from ..utils.rasterio import WGS84

log = logging.getLogger(__name__)


def harmonize_dtypes(gdfs: list[gpd.GeoDataFrame]) -> list[gpd.GeoDataFrame]:
    all_cols = set().union(*(gdf.columns for gdf in gdfs))
    all_cols.discard("geometry")
    for col in all_cols:
        # Check if any gdf has this column as object
        is_numeric = [col in gdf.columns and is_numeric_dtype(gdf[col]) for gdf in gdfs]
        is_object = [col in gdf.columns and is_object_dtype(gdf[col]) for gdf in gdfs]
        if any(is_numeric) and not all(is_numeric):
            log.debug(f"Converting {col} to numeric.")
            for gdf in gdfs:
                if col in gdf.columns:
                    gdf[col] = pd.to_numeric(gdf[col], errors="coerce")
        elif any(is_object) and not all(is_object):
            log.debug(f"Converting {col} to str.")
            for gdf in gdfs:
                if col in gdf.columns:
                    gdf[col] = gdf[col].astype(str)
    return gdfs


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

    # Workaround https://github.com/gbelouze/geefetch/issues/95
    gdfs = harmonize_dtypes(gdfs)
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

    # Workaround https://github.com/gbelouze/geefetch/issues/95
    gdfs = harmonize_dtypes(gdfs)
    return gpd.GeoDataFrame(pd.concat(gdfs))
