from abc import ABC, abstractmethod
from typing import Any, List

from geobbox import GeoBoundingBox

from ..downloadables import DownloadableABC

__all__ = ["SatelliteABC"]


class SatelliteABC(ABC):
    """Abstract base class for a satellite class, describing how to obtain data and various metadata
    about the satellite.
    """

    @abstractmethod
    def get(
        self, aoi: GeoBoundingBox, start_date: str, end_date: str, **kwargs: Any
    ) -> DownloadableABC:
        """Get downloadable data. It is up to the caller to make sure the computation will stay within the compute
        resource limit, e.g. if Google Earth Engine is used as a backend.
        """
        ...

    @abstractmethod
    def get_time_series(
        self, aoi: GeoBoundingBox, start_date: str, end_date: str, **kwargs: Any
    ) -> DownloadableABC:
        """Get downloadable data to fetch time series. It is up to the caller to make sure the computation will stay
        within the compute resource limit, e.g. if Google Earth Engine is used as a backend.
        """
        ...

    @property
    @abstractmethod
    def bands(self) -> List[str]:
        """List of all satellite bands."""
        ...

    @property
    @abstractmethod
    def selected_bands(self) -> List[str]:
        """List of selected satellite bands."""
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

    def __eq__(self, other):
        if not isinstance(other, SatelliteABC):
            raise ValueError(
                f"Cannot compare satellite with values of type {type(other)}."
            )
        return self.name == other.name

    def __str__(self) -> str:
        return self.name
