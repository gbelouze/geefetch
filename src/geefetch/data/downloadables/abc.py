from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List

from geobbox import GeoBoundingBox
from rasterio.crs import CRS

__all__ = ["DownloadableABC"]


class DownloadableABC(ABC):
    @abstractmethod
    def download(
        self,
        out: Path,
        region: GeoBoundingBox,
        crs: CRS,
        bands: List[str],
        **kwargs: Any,
    ) -> None:
        """Download data.

        Parameters
        ----------
        out : Path
            The file to download the data to.
        region : GeoBoundingBox
            The AOI.
        crs : CRS
            The CRS in which `region` is expressed and in which to express the data.
        bands : list[str]
            The bands (for images) or properties (for collections) to select for download.
        **kwargs
            Any additional necessary arguments.
        """
        ...
