import logging
from pathlib import Path
from typing import Any

import geopandas
import omegaconf
import pooch
import shapely
from omegaconf import OmegaConf
from rasterio.crs import CRS
from thefuzz import process

import geefetch
import geefetch.data.satellites as satellites
from geefetch import data
from geefetch.utils.config import git_style_diff

from .omegaconfig import SpeckleFilterConfig, TerrainNormalizationConfig, load

log = logging.getLogger(__name__)

COUNTRY_BORDERS_URL = (
    "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
    "world-administrative-boundaries/exports/geojson"
)


def load_country_filter_polygon(country: Any) -> shapely.Polygon | shapely.MultiPolygon | None:
    """Load the mailand shape of a country."""
    match country:
        case str():
            country = [country]
        case None | []:
            return None
        case list() if all(isinstance(x, str) for x in country):
            pass
        case _:
            raise TypeError(
                f"Unexpected type {type(country)} for country. "
                "Must be `str`, `list[str]` or `None`."
            )

    country_borders_path = pooch.retrieve(url=COUNTRY_BORDERS_URL, known_hash=None)
    log.debug(f"Country borders is downloaded to {country_borders_path}")
    country_borders = geopandas.read_file(country_borders_path)
    polygons = []
    for c in country:
        if c not in country_borders.name.values:
            best_match, _ = process.extractOne(c, country_borders.name.values)
            raise ValueError(f"Unknown country {c}. Did you mean {best_match} ?")
        borders = country_borders[country_borders.name == c].iloc[0].geometry
        polygons.append(borders)
    return shapely.ops.unary_union(polygons)


def save_config(
    config: Any,
    dir: Path,
) -> None:
    """When `geefetch` is called with a specified configuration file, save it to the tracker root"""
    dir.mkdir(exist_ok=True, parents=True)
    config_path = Path(dir / "config.yaml")
    config = OmegaConf.to_container(omegaconf.DictConfig(config))

    del config["gee"]["ee_project_ids"]
    config["geefetch_version"] = geefetch.__version__
    config_yaml = OmegaConf.to_yaml(config)
    if config_path.exists():
        saved_config_yaml = config_path.read_text()
        if saved_config_yaml != config_yaml:
            log.error(
                "Diff current config / saved config:\n"
                f"{git_style_diff(config_yaml, saved_config_yaml)}"
            )
            raise ValueError("Current config and saved config disagree. Aborting.")
    else:
        config_path.write_text(config_yaml)
        log.debug(f"Config file is saved to {config_path}.")


def download_gedi(config_path: Path, vector: bool) -> None:
    "Download GEDI images."
    config = load(config_path)
    if config.gedi is None:
        raise RuntimeError(
            "GEDI is not configured. Pass `gedi: {}` in the config file to use `satellite_default`."
        )
    data_dir = Path(config.data_dir)
    bounds = config.gedi.aoi.spatial.as_bbox()
    if vector:
        if config.gedi.selected_bands is None:
            config.gedi.selected_bands = satellites.GEDIvector().default_selected_bands

        save_config(config.gedi, config.data_dir / "gedi_vector")
        data.get.download_gedi_vector(
            data_dir,
            config.gedi.gee.ee_project_ids,
            bounds,
            config.gedi.aoi.temporal.start_date if config.gedi.aoi.temporal is not None else None,
            config.gedi.aoi.temporal.end_date if config.gedi.aoi.temporal is not None else None,
            config.gedi.selected_bands,
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
        if config.gedi.selected_bands is None:
            config.gedi.selected_bands = satellites.GEDIraster().default_selected_bands
        save_config(config.gedi, config.data_dir / "gedi_raster")
        data.get.download_gedi(
            data_dir,
            config.gedi.gee.ee_project_ids,
            bounds,
            config.gedi.aoi.temporal.start_date if config.gedi.aoi.temporal is not None else None,
            config.gedi.aoi.temporal.end_date if config.gedi.aoi.temporal is not None else None,
            config.gedi.selected_bands,
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
            "Sentinel-1 is not configured. "
            "Pass `s1: {}` in the config file to use `satellite_default`."
        )
    if config.s1.selected_bands is None:
        config.s1.selected_bands = satellites.S1().default_selected_bands
    save_config(config.s1, config.data_dir / "s1")

    data_dir = Path(config.data_dir)
    bounds = config.s1.aoi.spatial.as_bbox()

    assert config.s1.terrain_normalization is None or isinstance(
        config.s1.terrain_normalization, TerrainNormalizationConfig
    )
    assert config.s1.speckle_filter is None or isinstance(
        config.s1.speckle_filter, SpeckleFilterConfig
    )

    data.get.download_s1(
        data_dir,
        config.s1.gee.ee_project_ids,
        bounds,
        config.s1.aoi.temporal.start_date if config.s1.aoi.temporal is not None else None,
        config.s1.aoi.temporal.end_date if config.s1.aoi.temporal is not None else None,
        config.s1.selected_bands,
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
        speckle_filter_config=config.s1.speckle_filter,
        terrain_normalization_config=config.s1.terrain_normalization,
        orbit=config.s1.orbit,
        resampling=config.s1.resampling,
    )


def download_s2(config_path: Path) -> None:
    """Download Sentinel-2 images."""
    config = load(config_path)
    if config.s2 is None:
        raise RuntimeError(
            "Sentinel-2 is not configured. "
            "Pass `s2: {}` in the config file to use `satellite_default`."
        )
    if config.s2.selected_bands is None:
        config.s2.selected_bands = satellites.S2().default_selected_bands
    save_config(config.s2, config.data_dir / "s2")

    data_dir = Path(config.data_dir)
    bounds = config.s2.aoi.spatial.as_bbox()
    data.get.download_s2(
        data_dir,
        config.s2.gee.ee_project_ids,
        bounds,
        config.s2.aoi.temporal.start_date if config.s2.aoi.temporal is not None else None,
        config.s2.aoi.temporal.end_date if config.s2.aoi.temporal is not None else None,
        config.s2.selected_bands,
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
        resampling=config.s2.resampling,
    )


def download_dynworld(config_path: Path) -> None:
    """Download Dynamic World images."""
    config = load(config_path)
    if config.dynworld is None:
        raise RuntimeError(
            "Dynamic World is not configured. "
            "Pass `dynworld: {}` in the config file to use `satellite_default`."
        )
    if config.dynworld.selected_bands is None:
        config.dynworld.selected_bands = satellites.DynWorld().default_selected_bands
    save_config(config.dynworld, config.data_dir / "dyn_world")

    data_dir = Path(config.data_dir)
    bounds = config.dynworld.aoi.spatial.as_bbox()
    data.get.download_dynworld(
        data_dir,
        config.dynworld.gee.ee_project_ids,
        bounds,
        config.dynworld.aoi.temporal.start_date
        if config.dynworld.aoi.temporal is not None
        else None,
        config.dynworld.aoi.temporal.end_date if config.dynworld.aoi.temporal is not None else None,
        config.dynworld.selected_bands,
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
        resampling=config.dynworld.resampling,
    )


def download_landsat8(config_path: Path) -> None:
    """Download Landsat 8 images."""
    config = load(config_path)
    if config.landsat8 is None:
        raise RuntimeError(
            "Landsat 8 is not configured. "
            "Pass `landsat8: {}` in the config file to use `satellite_default`."
        )
    if config.landsat8.selected_bands is None:
        config.landsat8.selected_bands = satellites.Landsat8().default_selected_bands
    save_config(config.landsat8, config.data_dir / "landsat8")
    data_dir = Path(config.data_dir)
    bounds = config.landsat8.aoi.spatial.as_bbox()
    data.get.download_landsat8(
        data_dir,
        config.landsat8.gee.ee_project_ids,
        bounds,
        config.landsat8.aoi.temporal.start_date
        if config.landsat8.aoi.temporal is not None
        else None,
        config.landsat8.aoi.temporal.end_date if config.landsat8.aoi.temporal is not None else None,
        config.landsat8.selected_bands,
        crs=(
            CRS.from_epsg(config.landsat8.aoi.spatial.epsg)
            if config.landsat8.aoi.spatial.epsg
            != 4326  # Need to check why config.s1.aoi.spatial.epsg is used for all function
            else None
        ),
        composite_method=config.landsat8.composite_method,
        dtype=config.landsat8.dtype,
        resolution=config.landsat8.resolution,
        tile_shape=config.landsat8.tile_size,
        max_tile_size=config.landsat8.gee.max_tile_size,
        filter_polygon=(
            None
            if config.landsat8.aoi.country is None
            else load_country_filter_polygon(config.landsat8.aoi.country)
        ),
        resampling=config.landsat8.resampling,
    )


def download_palsar2(config_path: Path) -> None:
    """Download PALSAR-2 images."""
    config = load(config_path)
    if config.palsar2 is None:
        raise RuntimeError(
            "Palsar 2 is not configured. "
            "Pass `palsar2: {}` in the config file to use `satellite_default`."
        )
    if config.palsar2.selected_bands is None:
        config.palsar2.selected_bands = satellites.Palsar2().default_selected_bands
    save_config(config.palsar2, config.data_dir / "palsar2")
    data_dir = Path(config.data_dir)
    bounds = config.palsar2.aoi.spatial.as_bbox()
    data.get.download_palsar2(
        data_dir,
        config.palsar2.gee.ee_project_ids,
        bounds,
        config.palsar2.aoi.temporal.start_date if config.palsar2.aoi.temporal is not None else None,
        config.palsar2.aoi.temporal.end_date if config.palsar2.aoi.temporal is not None else None,
        config.palsar2.selected_bands,
        crs=(
            CRS.from_epsg(config.palsar2.aoi.spatial.epsg)
            if config.palsar2.aoi.spatial.epsg
            != 4326  # Need to check why config.s1.aoi.spatial.epsg is used for all function
            else None
        ),
        composite_method=config.palsar2.composite_method,
        dtype=config.palsar2.dtype,
        resolution=config.palsar2.resolution,
        tile_shape=config.palsar2.tile_size,
        max_tile_size=config.palsar2.gee.max_tile_size,
        filter_polygon=(
            None
            if config.palsar2.aoi.country is None
            else load_country_filter_polygon(config.palsar2.aoi.country)
        ),
        orbit=config.palsar2.orbit,
        resampling=config.palsar2.resampling,
        refined_lee=config.palsar2.refined_lee,
    )


def download_nasadem(config_path: Path) -> None:
    """Download NASADEM images."""
    config = load(config_path)
    if config.nasadem is None:
        raise RuntimeError(
            "NASADEM is not configured. "
            "Pass `nasadem: {}` in the config file to use `satellite_default`."
        )
    if config.nasadem.selected_bands is None:
        config.nasadem.selected_bands = satellites.NASADEM().default_selected_bands
    save_config(config.nasadem, config.data_dir / "nasadem")
    data_dir = Path(config.data_dir)
    bounds = config.nasadem.aoi.spatial.as_bbox()
    if config.nasadem.aoi.temporal is not None:
        log.warning(
            f"Temporal config {config.nasadem.aoi.temporal.start_date} "
            f"→ {config.nasadem.aoi.temporal.end_date} is ignored."
        )
    data.get.download_nasadem(
        data_dir,
        config.nasadem.gee.ee_project_ids,
        bounds,
        crs=(
            CRS.from_epsg(config.nasadem.aoi.spatial.epsg)
            if config.nasadem.aoi.spatial.epsg
            != 4326  # Need to check why config.s1.aoi.spatial.epsg is used for all function
            else None
        ),
        composite_method=config.nasadem.composite_method,
        dtype=config.nasadem.dtype,
        resolution=config.nasadem.resolution,
        tile_shape=config.nasadem.tile_size,
        max_tile_size=config.nasadem.gee.max_tile_size,
        filter_polygon=(
            None
            if config.nasadem.aoi.country is None
            else load_country_filter_polygon(config.nasadem.aoi.country)
        ),
        resampling=config.nasadem.resampling,
    )


def download_custom(config_path: Path, custom_name: str) -> None:
    """Download Custom images."""
    config = load(config_path)
    if config.customs is None or custom_name not in config.customs:
        raise RuntimeError(f"No configuration given for custom satellites {custom_name}.")
    custom_config = config.customs[custom_name]
    if custom_config.selected_bands is None:
        raise ValueError("`selected_bands` must be given for custom satellites.")
    satellite_custom = satellites.CustomSatellite(
        custom_config.url, custom_config.pixel_range, name=custom_name
    )
    save_config(custom_config, config.data_dir / satellite_custom.name)
    data_dir = Path(config.data_dir)
    bounds = custom_config.aoi.spatial.as_bbox()
    start_date = (
        custom_config.aoi.temporal.start_date if custom_config.aoi.temporal is not None else None
    )
    end_date = (
        custom_config.aoi.temporal.end_date if custom_config.aoi.temporal is not None else None
    )

    data.get.download_custom(
        satellite_custom,
        data_dir,
        custom_config.gee.ee_project_ids,
        bounds,
        start_date,
        end_date,
        crs=(
            CRS.from_epsg(custom_config.aoi.spatial.epsg)
            if custom_config.aoi.spatial.epsg != 4326
            else None
        ),
        composite_method=custom_config.composite_method,
        dtype=custom_config.dtype,
        resolution=custom_config.resolution,
        tile_shape=custom_config.tile_size,
        max_tile_size=custom_config.gee.max_tile_size,
        selected_bands=custom_config.selected_bands,
        filter_polygon=(
            None
            if custom_config.aoi.country is None
            else load_country_filter_polygon(custom_config.aoi.country)
        ),
        resampling=custom_config.resampling,
    )


def download_all(config_path: Path) -> None:
    """Download all configured satellites."""
    config = load(config_path, add_missing_sats=False)

    # Check which satellites were actually configured by the user
    if hasattr(config, "s1"):
        log.info("Downloading Sentinel-1 data.")
        download_s1(config_path)
    if hasattr(config, "s2"):
        log.info("Downloading Sentinel-2 data.")
        download_s2(config_path)
    if hasattr(config, "gedi"):
        log.info("Downloading GEDI data.")
        download_gedi(config_path, vector=True)
    if hasattr(config, "dynworld"):
        log.info("Downloading Dynamic World data.")
        download_dynworld(config_path)
    if hasattr(config, "palsar2"):
        log.info("Downloading Palsar-2 data.")
        download_palsar2(config_path)
    if hasattr(config, "landsat8"):
        log.info("Downloading Landsat-8 data.")
        download_landsat8(config_path)
    if hasattr(config, "nasadem"):
        log.info("Downloading NASADEM")
        download_nasadem(config_path)
    if hasattr(config, "customs"):
        for custom_name in config.customs:
            log.info(f"Downloading CustomSatellite({custom_name}).")
            download_custom(config_path, custom_name)
