from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from omegaconf import OmegaConf
from rasterio.crs import CRS

from ..utils.coords import BoundingBox
from ..utils.gee import CompositeMethod, DType, Format


@dataclass
class GEEConfig:
    ee_project_id: str = "my-ee-project"
    max_tile_size: int = (
        10  # in MB, decrease if User Memory Excess Error, choose highest possible otherwise.
    )
    composite_method: CompositeMethod = CompositeMethod.MEDIAN


@dataclass
class SpatialAOIConfig:
    left: float
    right: float
    top: float
    bottom: float
    epsg: int = 4326

    def as_bbox(self) -> BoundingBox:
        return BoundingBox(
            left=self.left,
            right=self.right,
            top=self.top,
            bottom=self.bottom,
            crs=CRS.from_epsg(self.epsg),
        )


@dataclass
class TemporalAOIConfig:
    start_date: str
    end_date: str


@dataclass
class AOIConfig:
    spatial: SpatialAOIConfig
    temporal: TemporalAOIConfig
    # The name of a line in geopandas.datasets "naturalearth_lowres"
    # ..see also: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
    # Used to filter further the AOI to a country boundaries
    country: Optional[str] = None


@dataclass
class SatelliteDefaultConfig:
    aoi: AOIConfig
    gee: GEEConfig
    # The pixel side length for downloaded images
    tile_size: int = 5_000
    # The resolution for downloaded images, in meters
    resolution: int = 10
    # The pixel data type. Using Uint over Float may speed up download.
    dtype: DType = DType.Float32


@dataclass
class GediConfig(SatelliteDefaultConfig):
    # Filetype for downloading vector GEDI
    format: Format = Format.CSV


@dataclass
class S1Config(SatelliteDefaultConfig):
    pass


@dataclass
class S2Config(SatelliteDefaultConfig):
    cloudless_portion: int = 40
    cloud_prb_threshold: int = 40


@dataclass
class DynWorldConfig(SatelliteDefaultConfig):
    pass


@dataclass
class Config:
    data_dir: Path
    satellite_default: SatelliteDefaultConfig
    gedi: Optional[GediConfig]
    s1: Optional[S1Config]
    s2: Optional[S2Config]
    dynworld: Optional[DynWorldConfig]

    def __post_init__(self):
        self.data_dir = self.data_dir.expanduser().absolute()


def post_omegaconf_load(config: Any) -> None:
    """Updates in place the missing satellites config with the default.

    Parameters
    ----------
    config : Config
        The config loaded by OmegaConf.
    """
    OmegaConf.resolve(config)
    config.gedi = (
        OmegaConf.merge(
            OmegaConf.structured(GediConfig), config.satellite_default, config.gedi
        )
        if "gedi" in config
        else None
    )
    config.s1 = (
        OmegaConf.merge(
            OmegaConf.structured(S1Config), config.satellite_default, config.s1
        )
        if "s1" in config
        else None
    )
    config.s2 = (
        OmegaConf.merge(
            OmegaConf.structured(S2Config), config.satellite_default, config.s2
        )
        if "s2" in config
        else None
    )
    config.dynworld = (
        OmegaConf.merge(
            OmegaConf.structured(DynWorldConfig),
            config.satellite_default,
            config.dynworld,
        )
        if "dynworld" in config
        else None
    )


def load(path: Path) -> Config:
    if path.is_dir():
        from_yaml = OmegaConf.merge(
            *[OmegaConf.load(file) for file in path.iterdir() if file.suffix == ".yaml"]
        )
    else:
        from_yaml = OmegaConf.load(path)
    post_omegaconf_load(from_yaml)
    from_structured = OmegaConf.structured(Config)
    merged = OmegaConf.merge(from_structured, from_yaml)
    return OmegaConf.to_object(merged)  # type: ignore
