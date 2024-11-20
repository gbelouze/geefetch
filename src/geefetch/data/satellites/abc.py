from abc import ABC, abstractmethod
from typing import Any

import ee
from geobbox import GeoBoundingBox

from ...utils.enums import DType
from ..downloadables import DownloadableABC

__all__ = ["SatelliteABC"]


class SatelliteABC(ABC):
    """Abstract base class for a satellite class, describing how to obtain data and various metadata
    about the satellite.
    """

    @abstractmethod
    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
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
        start_date: str,
        end_date: str,
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
    def pixel_range(self) -> tuple[float, float]:
        """The minimum and maximum values that pixels can take.

        When converting the image to another type, pixels outside of that value range will saturate.
        """
        raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, SatelliteABC):
            raise ValueError(f"Cannot compare satellite with values of type {type(other)}.")
        return self.name == other.name

    def __str__(self) -> str:
        return self.name

    def convert_image(self, im: ee.Image, dtype: DType) -> ee.Image:
        min_p, max_p = self.pixel_range
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
