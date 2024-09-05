import logging
from pathlib import Path
from typing import Any

import geopandas
import pooch
import shapely
from omegaconf import OmegaConf
from rasterio.crs import CRS

from geefetch import data
from geefetch.utils.config import git_style_diff
from geefetch.utils.gee import auth

from .omegaconfig import load

log = logging.getLogger(__name__)

COUNTRY_BORDERS_URL = (
    "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
    "world-administrative-boundaries/exports/geojson"
)

COUNTRY_BORDERS_SHA256 = (
    "1f7e8a98461fdc86f3a71ce87cdee32e9c99a4760a5a2456a30b777fd0ae487e"
)


def get_mainland_geometry(shape: shapely.Geometry) -> shapely.Polygon:
    """Get the largest geometry from a multipolygon-like shapely geometry."""
    match type(shape):
        case shapely.MultiPolygon:
            max_area, max_geom = 0, None
            for geom in shape.geoms:
                if geom.area > max_area:
                    max_area, max_geom = geom.area, geom
            if max_geom is None:
                raise ValueError("Empty shape.")
            return max_geom
        case shapely.Polygon:
            return shape
        case _:
            raise TypeError(
                f"Type {shape} cannot be interpreted as a country border shape."
            )


def load_country_filter_polygon(country: str) -> shapely.Polygon:
    """Load the mailand shape of a country."""
    country_borders_path = pooch.retrieve(
        url=COUNTRY_BORDERS_URL, known_hash=COUNTRY_BORDERS_SHA256
    )
    country_borders = geopandas.read_file(country_borders_path)
    if country not in country_borders.name.values:
        raise ValueError(f"Unknown country {country}")
    country_borders = country_borders[country_borders.name == country].iloc[0].geometry
    return get_mainland_geometry(country_borders)


def save_config(config: Any, dir: Path) -> None:
    """When `geefetch` is called with a specified configuration file, save it to the tracker root."""
    if not dir.exists():
        dir.mkdir()
    config_path = Path(dir / "config.yaml")
    config_yaml = OmegaConf.to_yaml(config)
    if config_path.exists():
        with open(config_path, "r") as saved_config_file:
            saved_config_yaml = saved_config_file.read()
            if saved_config_yaml != config_yaml:
                log.error(
                    f"Diff current config / saved config:\n{git_style_diff(config_yaml, saved_config_yaml)}"
                )
                raise ValueError("Current config and saved config disagree. Aborting.")
    else:
        with open(config_path, "w") as config_file:
            config_file.write(config_yaml)
            log.debug(f"Config file is saved to {config_path}.")


def download_gedi(config_path: Path, vector: bool) -> None:
    "Download GEDI images."
    config = load(config_path)
    if config.gedi is None:
        raise RuntimeError(
            "GEDI is not configured. Pass `gedi: {}` in the config file to use `satellite_default`."
        )

    data_dir = Path(config.data_dir)
    auth(config.gedi.gee.ee_project_id)
    bounds = config.gedi.aoi.spatial.as_bbox()
    if vector:
        save_config(config.gedi, config.data_dir / "gedi_vector")
        data.get.download_gedi_vector(
            data_dir,
            bounds,
            config.gedi.aoi.temporal.start_date,
            config.gedi.aoi.temporal.end_date,
            crs=(
                CRS.from_epsg(config.gedi.aoi.spatial.epsg)
                if config.gedi.aoi.spatial.epsg != 4326
                else None
            ),
            resolution=config.gedi.resolution,
            tile_shape=config.gedi.tile_size,
            filter_polygon=(
                None
                if config.gedi.aoi.country is None
                else load_country_filter_polygon(config.gedi.aoi.country)
            ),
            format=config.gedi.format,
        )
    else:
        save_config(config.gedi, config.data_dir / "gedi_raster")
        data.get.download_gedi(
            data_dir,
            bounds,
            config.gedi.aoi.temporal.start_date,
            config.gedi.aoi.temporal.end_date,
            crs=(
                CRS.from_epsg(config.gedi.aoi.spatial.epsg)
                if config.gedi.aoi.spatial.epsg != 4326
                else None
            ),
            composite_method=config.gedi.composite_method,
            dtype=config.gedi.dtype,
            resolution=config.gedi.resolution,
            tile_shape=config.gedi.tile_size,
            filter_polygon=(
                None
                if config.gedi.aoi.country is None
                else load_country_filter_polygon(config.gedi.aoi.country)
            ),
        )


def download_s1(config_path: Path) -> None:
    "Download Sentinel-1 images."
    config = load(config_path)
    if config.s1 is None:
        raise RuntimeError(
            "Sentinel-1 is not configured. Pass `s1: {}` in the config file to use `satellite_default`."
        )
    save_config(config.s1, config.data_dir / "s1")

    data_dir = Path(config.data_dir)
    auth(config.s1.gee.ee_project_id)
    bounds = config.s1.aoi.spatial.as_bbox()
    data.get.download_s1(
        data_dir,
        bounds,
        config.s1.aoi.temporal.start_date,
        config.s1.aoi.temporal.end_date,
        crs=(
            CRS.from_epsg(config.s1.aoi.spatial.epsg)
            if config.s1.aoi.spatial.epsg != 4326
            else None
        ),
        composite_method=config.s1.composite_method,
        dtype=config.s1.dtype,
        resolution=config.s1.resolution,
        tile_shape=config.s1.tile_size,
        max_tile_size=config.s1.gee.max_tile_size,
        filter_polygon=(
            None
            if config.s1.aoi.country is None
            else load_country_filter_polygon(config.s1.aoi.country)
        ),
    )


def download_s2(config_path: Path) -> None:
    """Download Sentinel-2 images."""
    config = load(config_path)
    if config.s2 is None:
        raise RuntimeError(
            "Sentinel-2 is not configured. Pass `s2: {}` in the config file to use `satellite_default`."
        )
    save_config(config.s2, config.data_dir / "s2")

    data_dir = Path(config.data_dir)
    auth(config.s2.gee.ee_project_id)
    bounds = config.s2.aoi.spatial.as_bbox()
    data.get.download_s2(
        data_dir,
        bounds,
        config.s2.aoi.temporal.start_date,
        config.s2.aoi.temporal.end_date,
        crs=(
            CRS.from_epsg(config.s2.aoi.spatial.epsg)
            if config.s2.aoi.spatial.epsg != 4326
            else None
        ),
        composite_method=config.s2.composite_method,
        dtype=config.s2.dtype,
        resolution=config.s2.resolution,
        tile_shape=config.s2.tile_size,
        max_tile_size=config.s2.gee.max_tile_size,
        filter_polygon=(
            None
            if config.s2.aoi.country is None
            else load_country_filter_polygon(config.s2.aoi.country)
        ),
        cloudless_portion=config.s2.cloudless_portion,
        cloud_prb_thresh=config.s2.cloud_prb_threshold,
    )


def download_dynworld(config_path: Path) -> None:
    """Download Dynamic World images."""
    config = load(config_path)
    if config.dynworld is None:
        raise RuntimeError(
            "Dynamic World is not configured. Pass `dynworld: {}` in the config file to use `satellite_default`."
        )
    save_config(config.dynworld, config.data_dir / "dyn_world")

    data_dir = Path(config.data_dir)
    auth(config.dynworld.gee.ee_project_id)
    bounds = config.dynworld.aoi.spatial.as_bbox()
    data.get.download_dynworld(
        data_dir,
        bounds,
        config.dynworld.aoi.temporal.start_date,
        config.dynworld.aoi.temporal.end_date,
        crs=(
            CRS.from_epsg(config.dynworld.aoi.spatial.epsg)
            if config.dynworld.aoi.spatial.epsg != 4326
            else None
        ),
        composite_method=config.dynworld.composite_method,
        dtype=config.dynworld.dtype,
        resolution=config.dynworld.resolution,
        tile_shape=config.dynworld.tile_size,
        max_tile_size=config.dynworld.gee.max_tile_size,
        filter_polygon=(
            None
            if config.dynworld.aoi.country is None
            else load_country_filter_polygon(config.dynworld.aoi.country)
        ),
    )


def download_all(config_path: Path) -> None:
    """Download all configured satellites."""
    config = load(config_path)
    if config.s1 is not None:
        log.info("Downloading Sentinel-1 data.")
        download_s1(config_path)
    if config.s2 is not None:
        log.info("Downloading Sentinel-2 data.")
        download_s2(config_path)
    if config.gedi is not None:
        log.info("Downloading GEDI data.")
        download_gedi(config_path, vector=True)
    if config.dynworld is not None:
        log.info("Downloading Dynamic World data.")
        download_dynworld(config_path)
