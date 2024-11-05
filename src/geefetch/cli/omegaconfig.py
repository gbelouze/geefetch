from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from geobbox import GeoBoundingBox
from omegaconf import OmegaConf
from rasterio.crs import CRS

from geefetch.utils.enums import CompositeMethod, DType, Format

__all__ = [
    "Config",
    "SatelliteDefaultConfig",
    "AOIConfig",
    "TemporalAOIConfig",
    "SpatialAOIConfig",
    "GEEConfig",
    "DynWorldConfig",
    "GediConfig",
    "S1Config",
    "S2Config",
    "load",
]


@dataclass
class GEEConfig:
    """Configuration of Google Earth Engine.

    Attributes
    ----------
    ee_project_id : str
        Your GEE id, to connect to the API.

        .. see also:: https://developers.google.com/earth-engine/apidocs/ee-initialize
    max_tile_size : int, optional
        Size constraint in MB for the request sent to GEE. This is heuristical and depends
        in general on what satellite you are interested in.
        Decrease if User Memory Excess Error, but choose highest possible otherwise. Defaults is 10.
    """

    ee_project_id: str = "my-ee-project"
    max_tile_size: int = 10


@dataclass
class SpatialAOIConfig:
    """Configuration of the spatial area of interest.

    Attributes
    ----------
    left : float
    right : float
    top : float
    bottom : float
    epsg : int, optional
        EPSG code for the CRS in which the boundaries are given. If given,
        the downloaded data will be expressed in that same CRS.
        Defaults is 4326, corresponding to WGS84 (latitude, longitude).
    """

    left: float
    right: float
    top: float
    bottom: float
    epsg: int = 4326

    def as_bbox(self) -> GeoBoundingBox:
        return GeoBoundingBox(
            left=self.left,
            right=self.right,
            top=self.top,
            bottom=self.bottom,
            crs=CRS.from_epsg(self.epsg),
        )


@dataclass
class TemporalAOIConfig:
    """Configuration of the temporal range of interest.

    Attributes
    ----------
    start_date : str
        Start date in 'YYYY-MM-DD' format.
    end_date : str
        End date in 'YYYY-MM-DD' format.
    """

    start_date: str
    end_date: str


@dataclass
class AOIConfig:
    """Configuration of a spatial/temporal Area of Interest (AOI).

    Attributes
    ----------
    spatial : SpatialAOIConfig
    temporal : TemporalAOIConfig
    country : Optional[str]
        The name of a country. If given, spatial AOI is further restricted to its area
        that intersects the country boundaries. Defaults to None.

        .. note:: See https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
            for possible values
    """

    spatial: SpatialAOIConfig
    temporal: TemporalAOIConfig
    # The name of a line in geopandas.datasets "naturalearth_lowres"
    # ..see also: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
    # Used to filter further the AOI to a country boundaries
    country: Optional[str] = None


@dataclass
class SatelliteDefaultConfig:
    """The structured type for a GeeFetch default satellite configuration

    Attributes
    ----------
    aoi : AOIConfig
        The temporal/spatial Area of Interest
    gee : GEEConfig
        Google Earth Engine specific configurationss
    tile_size : int
        The pixel side length for downloaded images
    resolution : int
        The resolution for downloaded images, in meters
    dtype : DType
        The data type for downloaded images. Can be used to
        reduce file size and download speed at the cost of
        some loss of precision.
    """

    aoi: AOIConfig
    gee: GEEConfig
    tile_size: int = 5_000
    resolution: int = 10
    dtype: DType = DType.Float32
    composite_method: CompositeMethod = CompositeMethod.MEDIAN


@dataclass
class GediConfig(SatelliteDefaultConfig):
    """The structured type for configuring GEDI.

    Attributes
    ----------
    format : Filetype for downloading vector GEDI
    """

    format: Format = Format.CSV


@dataclass
class S1Config(SatelliteDefaultConfig):
    """The structured type for configuring Sentinel-1."""

    pass


@dataclass
class S2Config(SatelliteDefaultConfig):
    """The structured type for configuring Sentinel-2.

    Attributes
    ----------
    cloudless_portion : int, optional
        Threshold for the portion of filled pixels that must be cloud/shadow free (%).
        Images that do not fullfill the requirement are filtered out before mosaicking.
    cloud_prb_thresh : int, optional
        Threshold for cloud probability above which a pixel is filtered out (%).
    """

    cloudless_portion: int = 40
    cloud_prb_threshold: int = 40


@dataclass
class DynWorldConfig(SatelliteDefaultConfig):
    """The structured type for configuring Dynamic World."""

    pass


@dataclass
class Landsat8Config(SatelliteDefaultConfig):
    """The structured type for configuring Landsat 8."""

    pass


@dataclass
class Palsar2Config(SatelliteDefaultConfig):
    """The structured type for configuring Landsat 8."""

    pass


@dataclass
class Config:
    """The structured type for a GeeFetch configuration.

    Attributes
    ----------
    data_dir : Path
        The path to store downloaded data.
    satellite_default : SatelliteDefaultConfig
        Default satellite configuration.
    gedi : GediConfig
        GEDI specific configuration / variation to the default.
    s1 : S1Config
        Sentinel-1 specific configuration / variation to the default.
    s2 : S2Config
        Sentinel-2 specific configuration / variation to the default.
    dynworld : DynWorldConfig
        Dynamic world specific configuration / variation to the default.
    landsat8 : Landsat8Config
        Landsat 8 specific configuration / variation to the default.
    palsar2 : Palsar2Config
        Palsar 2 specific configuration / variation to the default.
    """

    data_dir: Path
    satellite_default: SatelliteDefaultConfig
    gedi: Optional[GediConfig]
    s1: Optional[S1Config]
    s2: Optional[S2Config]
    dynworld: Optional[DynWorldConfig]
    landsat8: Optional[Landsat8Config]
    palsar2: Optional[Palsar2Config]

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
    config.landsat8 = (
        OmegaConf.merge(
            OmegaConf.structured(Landsat8Config),
            config.satellite_default,
            config.landsat8,
        )
        if "landsat8" in config
        else None
    )
    config.palsar2 = (
        OmegaConf.merge(
            OmegaConf.structured(Palsar2Config),
            config.satellite_default,
            config.palsar2,
        )
        if "palsar2" in config
        else None
    )


def load(path: Path) -> Config:
    """Load a config file."""
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
