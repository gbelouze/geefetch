import dataclasses
import logging
import types
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from string import Formatter
from typing import Any, Union, get_args, get_origin

import geopandas as gpd
import numpy as np
import pyproj
from geobbox import GeoBoundingBox
from omegaconf import DictConfig, ListConfig, OmegaConf
from omegaconf.errors import OmegaConfBaseException
from rasterio.crs import CRS

from geefetch.utils.enums import (
    CompositeMethod,
    DType,
    Format,
    P2Orbit,
    ResamplingMethod,
    S1Orbit,
)

log = logging.getLogger(__name__)

__all__ = [
    "GeefetchConfig",
    "SatelliteDefaultConfig",
    "AOIConfig",
    "TemporalAOIConfig",
    "SpatialAOIConfig",
    "GEEConfig",
    "DynWorldConfig",
    "GEDIL2AConfig",
    "GEDIL2BConfig",
    "S1Config",
    "S2Config",
    "load",
]


@dataclass
class GEEConfig:
    """Configuration of Google Earth Engine.

    Attributes
    ----------
    ee_project_ids : list[str]
        One or more GEE project id, to connect to the API. More project ids allow `geefetch`
        to process downloads in parallel.

        .. see also:: https://developers.google.com/earth-engine/apidocs/ee-initialize
    max_tile_size : float
        Size constraint in MB for the request sent to GEE. This is heuristical and depends
        in general on what satellite you are interested in.
        Decrease if User Memory Excess Error, but choose highest possible otherwise. Defaults is 10.
    """

    ee_project_ids: list[str] = field(default_factory=list)
    max_tile_size: float = 10


@dataclass
class BboxAOIConfig:
    """Configuration of simple rectangular spatial area of interest.

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

    left: float = -1
    right: float = -1
    top: float = -1
    bottom: float = -1

    epsg: int = 4326

    @property
    def crs(self) -> pyproj.CRS:
        return pyproj.CRS.from_epsg(self.epsg)

    def as_bbox(self) -> GeoBoundingBox:
        return GeoBoundingBox(
            left=self.left,
            bottom=self.bottom,
            right=self.right,
            top=self.top,
            crs=CRS.from_epsg(self.epsg),
        )


@dataclass
class GeofileAOIConfig:
    """Configuration of the spatial area of interest.

    Attributes
    ----------
    geofile : Path
        Path to a geofile readable by GeoPandas that contains one or more polygons
        that define the AOI.
    """

    geofile: Path

    def __after_init__(self):
        self._gdf = None

    @property
    def gdf(self) -> gpd.GeoDataFrame:
        if self._gdf is None:
            self._gdf = gpd.read_file(self.geofile)
        return self._gdf

    @property
    def crs(self) -> pyproj.CRS:
        return self.gdf.crs

    def as_bboxes(self, scale: int, tile_shape: int | None) -> list[GeoBoundingBox]:
        def snap(row):
            left, bottom, right, top = row

            left = np.floor(left / scale) * scale
            bottom = np.floor(bottom / scale) * scale
            if tile_shape:
                right = left + tile_shape * scale
                top = bottom + tile_shape * scale
            else:
                right = np.floor(right / scale) * scale
                top = np.floor(top / scale) * scale

            return left, bottom, right, top

        snapped = np.apply_along_axis(snap, 1, self.gdf.bounds.to_numpy())
        return [
            GeoBoundingBox(left, bottom, right, top, self.gdf.crs)
            for left, bottom, right, top in snapped
        ]


SpatialAOIConfig = BboxAOIConfig | GeofileAOIConfig


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
    country: str | list[str] | None = None


# `spatial` and `country` are union-typed and can't be handled by OmegaConf
# directly; they're relaxed to `Any` a few classes below -- see `UNION_FIELDS`.


@dataclass
class FileNamingConfig:
    """The structure type for the naming configuration of the downloaded files.
    With this config, we can format downloaded data with the following structure:

    data_dir / sub_root_dir / tile_dir_format / tile_stem_format

    data_dir is pulled from the GeeFetchConfig.
    The sub_root_dir is expected to be a string with no placeholders.

    If you are downloading data with a geo file as aoi configuration,
    you can use any parameter from the file to customize your tile names
    and their directories (if you want them in seperate directories that is.)

    tile_dir_format and tile_stem_format can be passed as parametrized strings.
    The variables passed as string parameters should share names with the geofiles parameters.

    Example
    -------
    tile_dir_format = "Continent-{continent}|UTM_Zone-{utm}"
    tile_stem_format = "{id}"

    For the formats above to work,
    the geo file passed in SpatialAOI should figure continent, utm and id columns.


    Attributes
    ----------
    sub_root_dir: str | None
        Subroot directory. Defaults to None
    tile_dir_format: str | None
        Tile directory format. Defaults to None
    tile_stem_format: str | None
        Tile stem format. Defaults to None
    """

    sub_root_dir: str | None = None
    tile_dir_format: str | None = None
    tile_stem_format: str | None = None

    def get_naming_dict(
        self, bboxes: list[GeoBoundingBox], gdf: gpd.GeoDataFrame
    ) -> dict[GeoBoundingBox, dict[str, Any]]:
        """

        Parameters
        ----------
        bboxes : list[GeoBoundingBox]
        gdf : gpd.GeoDataFrame
        Returns
        -------
        dict[GeoBoundingBox, dict[str, Any]]
        """
        # TODO: fix naming config without tile naming as it breaks geofile loading
        # TODO: Fix the fact that if the gdf or list of bboxes
        # change in order the dictionary won't properly match stuff
        # This function could actually be merged with the spatial AOI
        # to have the naming_properties extracted with the GeoBounding
        # boxes row per row, that way there is no risk to mismatch bounding boxes and gdf rows
        parametrized_string = (self.tile_dir_format or "") + (self.tile_stem_format or "")
        naming_properties = list(
            {var for _, var, _, _ in Formatter().parse(parametrized_string) if var}
        )
        values = gdf[naming_properties].to_dict(orient="records")
        return dict(zip(bboxes, values, strict=False))


@dataclass
class SatelliteDefaultConfig:
    """The structured type for a GeeFetch default satellite configuration

    Attributes
    ----------
    aoi : AOIConfig
        The temporal/spatial Area of Interest
    gee : GEEConfig
        Google Earth Engine specific configurations
    tile_shape : int | None
        The pixel side length for downloaded images. Defaults to 500 pixels.
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
    spectral_indices: list[str] | None
        The list of spectral indices to compute and add as bands of the downloaded images.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    file_naming_config : FileNamingConfig | None
        File naming configuration. Defaults to None.
    """

    aoi: AOIConfig
    gee: GEEConfig
    tile_shape: int | None = 5_00
    resolution: int = 10
    dtype: DType = DType.Float32
    composite_method: CompositeMethod = CompositeMethod.MEDIAN
    selected_bands: list[str] | None = None
    spectral_indices: list[str] | None = None
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR
    file_naming_config: FileNamingConfig | None = None


@dataclass
class GEDIL2AConfig(SatelliteDefaultConfig):
    """The structured type for configuring GEDI L2A.

    Attributes
    ----------
    format : Format
        Filetype for downloading vector GEDI. Defaults to Format.PARQUET
    """

    format: Format = Format.PARQUET


@dataclass
class GEDIL2BConfig(SatelliteDefaultConfig):
    """The structured type for configuring GEDI L2B.
    Attributes
    ----------
    format : Format
        Filetype for downloading vector GEDI. Defaults to Format.PARQUET
    """

    format: Format = Format.PARQUET


@dataclass
class TerrainNormalizationConfig:
    """The structured type to configure terrain normalization

    Attributes
    ----------
    flattening_model : str
        The radiometric terrain normalization model, either VOLUME or DIRECT
    layover_shadow_buffer :  int
        The additional buffer to account for the passive layover and shadow
    dem : str
        Digital elevation Model used for terrain corrections
    """

    flattening_model: str = "VOLUME"
    layover_shadow_buffer: int = 3
    dem: str = "USGS/SRTMGL1_003"


@dataclass
class SpeckleFilterConfig:
    """The structured type for configuring speckle
    Speckle filter configuration to apply to Sentinel-1

    Attributes
    ----------
    framework : str
        MONO for mono temporal filtering, MULTI for multi temporal.
    filter_name : str
        Name of the filter to use. BOXCAR, LEE, REFINED LEE, LEE SIGMA, GAMMA MAP.
    kernel_size : int
        Size of the filter kernel.
    nr_of_images : int
        If the MULTI framework is used, it will use this number of
        temporal neighbouring images per filtered image.
    """

    framework: str = "MONO"
    filter_name: str = "BOXCAR"
    kernel_size: int = 3
    nr_of_images: int = 10


class _Default(Enum):
    DEFAULT = "default"


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
    speckle_filter : SpeckleFilterConfig | _Default | None
        Configuration dataclass for speckle filtering, or None for no speckle filtering.
        Can also be "default" to use baseline speckle filtering parameters.
        Defaults to None.
    terrain_normalization : TerrainNormalizationConfig | _Default | None
        Configuration dataclass for terrain normalization, or None for no terrain normalization.
        Defaults to "default" which uses baseline terrain normalization parameters.
    """

    # using enum while https://github.com/omry/omegaconf/issues/422 is open
    orbit: S1Orbit = S1Orbit.BOTH
    speckle_filter: SpeckleFilterConfig | _Default | None = None
    terrain_normalization: TerrainNormalizationConfig | _Default | None = _Default.DEFAULT


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
    n_least_cloudy_monthly : int | None
        The number of least cloudy images to keep.
        This attribute is only used for TimeSeries and bypasses the
        cloudless_portion and cloud_prb_threshold attributes.
    add_cloud_mask : bool
        Wether to add to the image collection a cloud mask created with
        GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED. Defaults to False.
    """

    cloudless_portion: int = 40
    cloud_prb_threshold: int = 40
    n_least_cloudy_monthly: int | None = None
    # TODO Make add_cloud_mask a tuple with boolean and mask threshold
    add_cloud_mask: bool = False


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
    refined_lee : bool
        Whether to apply the Refined Lee filter to reduce speckle noise.
        Defaults to True.
    """

    orbit: P2Orbit = P2Orbit.DESCENDING
    refined_lee: bool = True


@dataclass
class NASADEMConfig(SatelliteDefaultConfig):
    """The structured type for configuring NASADEM."""


@dataclass
class CustomSatelliteConfig(SatelliteDefaultConfig):
    """The structured type for configuring a custom GEE dataset source.

    Attributes
    ----------
    url : str
        The Google Earth Engine id to access the satellite. Example: "NASA/NASADEM_HGT/001"
    pixel_range : tuple[float, float]
        The (min, max) range of pixel values. Used to normalize the custom satellite data.

    """

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
    gedi_l2a : GEDIL2AConfig
        GEDI specific configuration / variation to the default.
    gedi_l2b : GEDIL2BConfig
        GEDI L2B specific configuration / variation to the default.
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
    gedi_l2a: GEDIL2AConfig
    gedi_l2b: GEDIL2BConfig
    s1: S1Config
    s2: S2Config
    dynworld: DynWorldConfig
    landsat8: Landsat8Config
    palsar2: Palsar2Config
    nasadem: NASADEMConfig
    customs: dict[str, CustomSatelliteConfig]

    def __post_init__(self):
        self.data_dir = self.data_dir.expanduser().absolute()


# OmegaConf does not support union of containers types
# https://github.com/omry/omegaconf/issues/144
#
# Workaround: we relax exactly those fields to `Any` so `OmegaConf.structured` /
# `OmegaConf.merge` handle every *other* field on the class normally, then
# manually resolve the relaxed fields afterwards against their real annotation.
#
# `UNION_FIELDS` holds which fields need this. Their real annotations are read
# back off the classes before we override them with `Any`.
#
# Once `OmegaConf.to_object` has built the config, `_resolve_config_unions` walks
# the whole object tree once and resolves every node whose type is registered in
# `_UNION_ANNOTATIONS`.

UNION_FIELDS: dict[type, tuple[str, ...]] = {
    AOIConfig: ("spatial", "country"),
    S1Config: ("speckle_filter", "terrain_normalization"),
}

#: {cls: {field name: original annotation}}, filled by `relax_union_annotations`.
_UNION_ANNOTATIONS: dict[type, dict[str, Any]] = {}


def relax_union_annotations(cls: type, names: tuple[str, ...]) -> None:
    """Record `cls`'s real annotations for `names`, then weaken them to `Any`, in place.

    Parameters
    ----------
    cls : type
        The dataclass to patch.
    names : tuple[str, ...]
        Names of `cls`'s fields whose annotation is a union OmegaConf can't build
        a schema through. Each field's current annotation is stashed in
        `_UNION_ANNOTATIONS[cls]` and then replaced by `Any` so
        `OmegaConf.structured`/`merge` never sees the union; `resolve_union`
        reads the real annotation back from `_UNION_ANNOTATIONS` afterwards.
    """
    captured = _UNION_ANNOTATIONS.setdefault(cls, {})
    for name in names:
        captured[name] = cls.__annotations__[name]
        cls.__annotations__[name] = Any


for _cls, _names in UNION_FIELDS.items():
    relax_union_annotations(_cls, _names)


class UnionResolutionError(ValueError):
    """Raised when a config value doesn't validate against any member of a union type.

    Mirrors jsonargparse's behaviour for `Dataclass1 | Dataclass2`-typed arguments:
    every member of the union is tried in declaration order, and if none match,
    every member's failure is reported together so it's clear why each was rejected.
    """

    def __init__(self, annotation: Any, data: Any, errors: dict[str, Exception]) -> None:
        self.annotation = annotation
        self.data = data
        self.errors = errors
        lines = [f"  - {name}: {err}" for name, err in errors.items()]
        super().__init__(
            f"{data!r} does not validate against any member of {annotation}:\n" + "\n".join(lines)
        )


def resolve_union(annotation: Any, data: Any) -> Any:
    """Resolve `data` against a `Union[...]` type hint without a discriminator field.

    Tries each member of the union in declaration order and returns the first one
    that validates: dataclass members are validated via
    `OmegaConf.merge(OmegaConf.structured(member), data)`, `None` matches only
    `data is None`, and any other type (e.g. `str`, `list[str]`) is checked with `isinstance`.

    Raises `UnionResolutionError`, reporting every member's failure, if nothing matches.

    Parameters
    ----------
    annotation : Any
        A `Union` or `X | Y` type hint, or a single non-union type.
    data : Any
        The raw config value to resolve (e.g. an `omegaconf.DictConfig`, or a
        plain Python value).

    Returns
    -------
    Any
        The resolved value: a dataclass instance, `None`, or the raw value itself.
    """
    is_union = get_origin(annotation) in (Union, types.UnionType)
    members = get_args(annotation) if is_union else (annotation,)
    errors: dict[str, Exception] = {}

    for member in members:
        if dataclasses.is_dataclass(member):
            try:
                merged = OmegaConf.merge(OmegaConf.structured(member), data)
                return OmegaConf.to_object(merged)
            except (OmegaConfBaseException, ValueError, TypeError) as e:
                # ValueError/TypeError: `data` isn't even container-shaped (e.g. a
                # bare string), so OmegaConf.merge rejects it before any
                # OmegaConf-specific validation gets a chance to run.
                errors[member.__name__] = e  # type: ignore[union-attr]
            continue

        plain_data = (
            OmegaConf.to_container(data, resolve=True) if OmegaConf.is_config(data) else data
        )
        origin = get_origin(member) or member
        try:
            if isinstance(plain_data, origin):
                return plain_data
        except TypeError:
            pass
        errors[str(member)] = ValueError(f"{data!r} is not a {member}")

    raise UnionResolutionError(annotation, data, errors)


def _resolve_relaxed_unions(obj: Any) -> None:
    """Resolve every field of `obj` that `UNION_FIELDS` relaxed to `Any`, in place.

    Looks `type(obj)` up in `_UNION_ANNOTATIONS` and runs `resolve_union` on each
    recorded field against its original annotation. A no-op for types absent from
    `UNION_FIELDS`.
    """
    for name, annotation in _UNION_ANNOTATIONS.get(type(obj), {}).items():
        setattr(obj, name, resolve_union(annotation, getattr(obj, name)))


def _resolve_config_unions(node: Any) -> None:
    """Resolve every field relaxed by `UNION_FIELDS`, everywhere in the config.

    Walks the object graph built by `OmegaConf.to_object` once, pre-order: for
    every dataclass node whose `type(...)` is registered in `_UNION_ANNOTATIONS`
    ig`, `S1Config`) it resolves that node's recorded fields then recurses through
    dataclass fields, `dict` values and `list`/`tuple` items.
    Everything else (scalars, `Enum`, `Path`, `str`, `None`) is a leaf.
    """
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        _resolve_relaxed_unions(node)

        # `dataclasses.fields`, rather than `vars`/properties, so lazy attributes
        # such as `GeofileAOIConfig.gdf` (which reads a file) are never triggered.
        for f in dataclasses.fields(node):
            _resolve_config_unions(getattr(node, f.name))
    elif isinstance(node, dict):
        for value in node.values():
            _resolve_config_unions(value)
    elif isinstance(node, list | tuple):
        for item in node:
            _resolve_config_unions(item)


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

    config.gedi_l2a = OmegaConf.merge(
        OmegaConf.structured(GEDIL2AConfig),
        config.satellite_default,
        config.gedi_l2a if "gedi_l2a" in config else {},
    )
    config.gedi_l2b = OmegaConf.merge(
        OmegaConf.structured(GEDIL2BConfig),
        config.satellite_default,
        config.gedi_l2b if "gedi_l2b" in config else {},
    )
    config.s1 = OmegaConf.merge(
        OmegaConf.structured(S1Config),
        config.satellite_default,
        config.s1 if "s1" in config else {},
    )

    if config.s1.terrain_normalization in (_Default.DEFAULT, "default"):
        config.s1.terrain_normalization = TerrainNormalizationConfig()
    if config.s1.speckle_filter in (_Default.DEFAULT, "default"):
        config.s1.speckle_filter = SpeckleFilterConfig()

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


def load(path: Path, add_missing_sats: bool = True) -> GeefetchConfig:
    """Loads and validates a geefetch configuration from a YAML file or directory.

    If a directory is provided, all `.yaml` files within it are merged. The function
    then injects missing satellite configurations with defaults.

    Parameters
    ----------
    path : Path
        Path to a YAML file or a directory containing YAML files to load.
    add_missing_sats : bool, optional
        Whether to inject missing satellite configurations with defaults. Defaults to True.

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
    if not add_missing_sats:
        return from_yaml  # type: ignore
    _post_omegaconf_load(from_yaml)
    from_structured = OmegaConf.structured(GeefetchConfig)
    merged = OmegaConf.merge(from_structured, from_yaml)
    if merged.satellite_default.selected_bands is not None:
        raise ValueError("Selected bands should not be specified for default satellite.")
    result: GeefetchConfig = OmegaConf.to_object(merged)  # type: ignore[invalid-assignment, unused-ignore]
    _resolve_config_unions(result)
    return result
