import logging
from abc import ABC, abstractmethod
from typing import Any

from ee.image import Image
from geobbox import GeoBoundingBox

from ...utils.enums import DType, ResamplingMethod
from ...utils.rasterio import WGS84
from ..downloadables import DownloadableABC

log = logging.getLogger(__name__)

__all__ = ["SatelliteABC"]


class SatelliteABC(ABC):
    """Abstract base class for a satellite class, describing how to obtain data and various metadata
    about the satellite.
    """

    @abstractmethod
    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> DownloadableABC:
        """Get downloadable data. It is up to the caller to make sure the computation will stay
        within the compute resource limit, e.g. if Google Earth Engine is used as a backend.
        """
        ...

    @abstractmethod
    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> DownloadableABC:
        """Get downloadable data to fetch time series. It is up to the caller to make sure
        the computation will stay within the compute resource limit,
        e.g. if Google Earth Engine is used as a backend.
        """
        ...

    @property
    def bands(self) -> list[str]:
        """List of all satellite bands."""
        raise NotImplementedError

    @property
    @abstractmethod
    def default_selected_bands(self) -> list[str]:
        """List of default selected satellite bands."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """A string id of the satellite. Can be used in file names."""
        ...

    @property
    @abstractmethod
    def full_name(self) -> str:
        """A human readable string representation of the satellite."""
        ...

    @property
    @abstractmethod
    def is_raster(self) -> bool: ...

    @property
    def is_vector(self) -> bool:
        return not self.is_raster

    @property
    def pixel_range(self) -> tuple[float, float] | dict[str, tuple[float, float]]:
        """The minimum and maximum values that pixels can take.

        When converting the image to another type, pixels outside of that value range will saturate.
        Can be given as a (min, max) tuple (for every band), or as band specific (min, max) tuples.
        """
        raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, SatelliteABC):
            raise ValueError(f"Cannot compare satellite with values of type {type(other)}.")
        return self.name == other.name

    def __str__(self) -> str:
        return self.name

    def convert_dtype(self, im: Image, dtype: DType) -> Image:
        """Convert the image to the specified data type, applying the pixel range.

        Parameters
        ----------
        im : Image
            The image to convert.
        dtype : DType
            The target data type.

        Returns
        -------
        Image
            The converted (and optionally resampled) image.
        """

        pixel_range = self.pixel_range
        match pixel_range:
            case tuple():
                min_p, max_p = pixel_range
                im = im.clamp(min_p, max_p)
                match dtype:
                    case DType.Float32:
                        return im
                    case DType.UInt16:
                        return im.add(-min_p).multiply((2**16 - 1) / (max_p - min_p)).toUint16()
                    case DType.UInt8:
                        return im.add(-min_p).multiply((2**8 - 1) / (max_p - min_p)).toUint8()
                    case _:
                        raise ValueError(f"Unsupported {dtype=}.")
            case dict():
                band_names: list[str] = im.bandNames().getInfo()  # type: ignore[assignment]
                band_types: dict[str, Any] = im.bandTypes().getInfo()  # type: ignore[assignment]
                for band, (min_p, max_p) in pixel_range.items():
                    if band not in band_names:
                        log.warning(f"Band name {band} is not a recognized band name. Ignoring it.")
                        continue
                    if band not in band_types:
                        log.warning(f"Unkwown pixel type for band {band}.")
                        band_type = None
                    else:
                        band_type = band_types[band]
                    band_im = im.select(band).clamp(min_p, max_p)
                    match dtype:
                        case DType.Float32:
                            pass
                        case DType.UInt16:
                            if not (
                                (0 <= min_p < max_p <= 2**16 - 1)
                                and band_type is not None
                                and band_type["precision"] == "int"
                            ):
                                band_im = (
                                    band_im.add(-min_p)
                                    .multiply((2**16 - 1) / (max_p - min_p))
                                    .toUint16()
                                )
                            else:
                                band_im = band_im.toUint16()
                        case DType.UInt8:
                            if not (
                                (0 <= min_p < max_p <= 2**8 - 1)
                                and band_type is not None
                                and band_type["precision"] == "int"
                            ):
                                band_im = (
                                    band_im.add(-min_p)
                                    .multiply((2**8 - 1) / (max_p - min_p))
                                    .toUint8()
                                )
                            else:
                                band_im = band_im.toUint8()
                        case _:
                            raise ValueError(f"Unsupported {dtype=}.")
                    im = im.addBands(band_im, overwrite=True)
                return im
            case _:
                raise TypeError(f"Unexpected type {type(pixel_range)} for satellite's pixel range.")

    def check_selected_bands(self, bands: list[str]) -> None:
        """Check that a selection of bands is a subset of the satellite's bands."""
        unknown_bands = set(bands) - set(self.bands)
        if len(unknown_bands) > 0:
            raise ValueError(f"Unknown bands {unknown_bands} for satellite {self.full_name}.")

    @staticmethod
    def resample_reproject_clip(
        im: Image,
        aoi: GeoBoundingBox,
        resampling: ResamplingMethod,
        scale: float,
    ) -> Image:
        match resampling:
            case ResamplingMethod.BILINEAR | ResamplingMethod.BICUBIC:
                im = im.resample(resampling.value)
            case ResamplingMethod.NEAREST:
                pass
            case _:
                raise ValueError(f"Cannot reproject with method {resampling}")
        im = im.reproject(crs=aoi.crs.to_string(), scale=scale)
        bounds = aoi.transform(WGS84).to_ee_geometry()
        return im.clip(bounds)
