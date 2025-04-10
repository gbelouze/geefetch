from dataclasses import dataclass
from pathlib import Path
from typing import Any

from geobbox import GeoBoundingBox
from omegaconf import DictConfig, ListConfig, OmegaConf
from rasterio.crs import CRS

from geefetch.utils.enums import CompositeMethod, DType, Format, P2Orbit, S1Orbit

__all__ = [
    "GeefetchConfig",
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
    max_tile_size : int
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
    epsg : int
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
class AOIConfig:  # noqa: 605
    """Configuration of a spatial/temporal Area of Interest (AOI).

    Attributes
    ----------
    spatial : SpatialAOIConfig
    temporal : TemporalAOIConfig | None
    country : str | list[str] | None
        The name of one or more countries. If given, spatial AOI is further restricted to its area
        that intersects one of the country boundaries. Defaults to None.

        .. note:: See https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
            for possible values
    """

    spatial: SpatialAOIConfig
    temporal: TemporalAOIConfig | None

    # The name of a line in geopandas.datasets "naturalearth_lowres"
    # ..see also: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
    # Used to further filter the AOI to a country boundaries
    # Currently limited by https://github.com/omry/omegaconf/issues/144
    # so we can't type check
    country: Any = None


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
    composite_method : CompositeMethod
        The mosaicking method. Use CompositeMethod.TIMESERIES
        to download time series instead of mosaicks. Defaults
        to CompositeMethod.MEDIAN.
    selected_bands : list[str] | None
        The bands to download. If None, will use the satellite
        default bands. Defaults to None.
    """

    aoi: AOIConfig
    gee: GEEConfig
    tile_size: int = 5_000
    resolution: int = 10
    dtype: DType = DType.Float32
    composite_method: CompositeMethod = CompositeMethod.MEDIAN
    selected_bands: list[str] | None = None


@dataclass
class GediConfig(SatelliteDefaultConfig):
    """The structured type for configuring GEDI.

    Attributes
    ----------
    format : Format
        Filetype for downloading vector GEDI. Defaults to Format.PARQUET
    """

    format: Format = Format.PARQUET


@dataclass
class S1Config(SatelliteDefaultConfig):
    """The structured type for configuring Sentinel-1.

    Attributes
    ----------
    orbit : S1Orbit
        Orbit direction to filter Sentinel-1 acquisitions.
        Can be ASCENDING, DESCENDING, BOTH, or AS_BANDS
        to download ascending and descending composites as separate bands.
        Defaults to BOTH.
    """

    # using enum while https://github.com/omry/omegaconf/issues/422 is open
    orbit: S1Orbit = S1Orbit.BOTH


@dataclass
class S2Config(SatelliteDefaultConfig):
    """The structured type for configuring Sentinel-2.

    Attributes
    ----------
    cloudless_portion : int
        Threshold for the portion of filled pixels that must be cloud/shadow free (%).
        Images that do not fullfill the requirement are filtered out before mosaicking.
        Default is 40.
    cloud_prb_threshold : int
        Threshold for cloud probability above which a pixel is filtered out (%). Default is 40.
    """

    cloudless_portion: int = 40
    cloud_prb_threshold: int = 40


@dataclass
class DynWorldConfig(SatelliteDefaultConfig):
    """The structured type for configuring Dynamic World."""


@dataclass
class Landsat8Config(SatelliteDefaultConfig):
    """The structured type for configuring Landsat 8."""


@dataclass
class Palsar2Config(SatelliteDefaultConfig):
    """The structured type for configuring Palsar 2.

    Attributes
    ----------
    orbit : P2Orbit
        Orbit direction to filter PALSAR-2 acquisitions.
        Can be ASCENDING or DESCENDING. Defaults to DESCENDING.
    """

    orbit: P2Orbit = P2Orbit.DESCENDING


@dataclass
class NASADEMConfig(SatelliteDefaultConfig):
    """The structured type for configuring NASADEM."""


@dataclass
class CustomSatelliteConfig(SatelliteDefaultConfig):
    """The structured type for configuring a custom GEE dataset source."""

    url: str = "unknown"
    pixel_range: tuple[float, float] = (-1, -1)

    def __post_init__(self):
        if self.url == "unknown":
            raise ValueError("Argument `url` must be given.")
        self.pixel_range = tuple(self.pixel_range)  # type: ignore[assignment]
        if self.pixel_range == (-1, -1):
            raise ValueError("Argument `pixel_range` must be given.")


@dataclass
class GeefetchConfig:
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
    nasadem : NASADEMConfig
        NASA-DEM specific configuration / variation to the default.
    customs : dict[str, CustomSatelliteConfig]
        Configuration for a specific dataset sources unsupported natively by `geefetch`.
    """

    data_dir: Path
    satellite_default: SatelliteDefaultConfig
    gedi: GediConfig
    s1: S1Config
    s2: S2Config
    dynworld: DynWorldConfig
    landsat8: Landsat8Config
    palsar2: Palsar2Config
    nasadem: NASADEMConfig
    customs: dict[str, CustomSatelliteConfig]

    def __post_init__(self):
        self.data_dir = self.data_dir.expanduser().absolute()


def _post_omegaconf_load(config: DictConfig | ListConfig) -> None:
    """Post-processes a loaded OmegaConf config by merging satellite defaults.

    This function updates the configuration in place by merging default satellite
    parameters into each satellite-specific configuration (GEDI, Sentinel-1, Sentinel-2, etc.).
    If custom satellites are defined, they are also merged with the default template.

    Parameters
    ----------
    config : DictConfig | ListConfig
        A configuration object loaded using OmegaConf, expected to include
        a `satellite_default` section and optionally sections for each known
        satellite or user-defined `customs`.
    """
    OmegaConf.resolve(config)

    config.gedi = OmegaConf.merge(
        OmegaConf.structured(GediConfig),
        config.satellite_default,
        config.gedi if "gedi" in config else {},
    )
    config.s1 = OmegaConf.merge(
        OmegaConf.structured(S1Config),
        config.satellite_default,
        config.s1 if "s1" in config else {},
    )
    config.s2 = OmegaConf.merge(
        OmegaConf.structured(S2Config),
        config.satellite_default,
        config.s2 if "s2" in config else {},
    )
    config.dynworld = OmegaConf.merge(
        OmegaConf.structured(DynWorldConfig),
        config.satellite_default,
        config.dynworld if "dynworld" in config else {},
    )
    config.landsat8 = OmegaConf.merge(
        OmegaConf.structured(Landsat8Config),
        config.satellite_default,
        config.landsat8 if "landsat8" in config else {},
    )
    config.palsar2 = OmegaConf.merge(
        OmegaConf.structured(Palsar2Config),
        config.satellite_default,
        config.palsar2 if "palsar2" in config else {},
    )

    config.nasadem = OmegaConf.merge(
        OmegaConf.structured(NASADEMConfig),
        config.satellite_default,
        config.nasadem if "nasadem" in config else {},
    )

    if "customs" in config:
        if not isinstance(config.customs, DictConfig):
            raise ValueError(
                "Invalid configuration for `customs`. "
                f"Expected dict-like, got {type(config.customs)}."
            )
        config.customs = {
            custom_name: OmegaConf.merge(
                OmegaConf.structured(CustomSatelliteConfig), config.satellite_default, custom_config
            )
            for custom_name, custom_config in config.customs.items()
        }
    else:
        config.customs = {}


def load(path: Path) -> GeefetchConfig:
    """Loads and validates a geefetch configuration from a YAML file or directory.

    If a directory is provided, all `.yaml` files within it are merged. The function
    then injects missing satellite configurations with defaults.

    Parameters
    ----------
    path : Path
        Path to a YAML file or a directory containing YAML files to load.

    Returns
    -------
    GeefetchConfig
        The fully merged and validated configuration object.
    """
    if path.is_dir():
        from_yaml = OmegaConf.merge(
            *[OmegaConf.load(file) for file in path.iterdir() if file.suffix == ".yaml"]
        )
    else:
        from_yaml = OmegaConf.load(path)
    _post_omegaconf_load(from_yaml)
    from_structured = OmegaConf.structured(GeefetchConfig)
    merged = OmegaConf.merge(from_structured, from_yaml)
    if merged.satellite_default.selected_bands is not None:
        raise ValueError("Selected bands should not be specified for default satellite.")
    return OmegaConf.to_object(merged)  # type: ignore
