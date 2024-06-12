from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List

import ee
from rasterio.crs import CRS


class DownloadableABC(ABC):
    @abstractmethod
    def download(
        self, out: Path, region: ee.Geometry, crs: CRS, bands: List[str], **kwargs: Any
    ) -> None:
        """Download data.

        Parameters
        ----------
        out : Path
            The file to download the data to.
        region : ee.Geometry
            The AOI.
        crs : CRS
            The CRS in which `region` is expressed and in which to express the data.
        bands : list[str]
            The bands (for images) or properties (for collections) to select for download.
        **kwargs
            Any additional necessary arguments.
        """
        ...
