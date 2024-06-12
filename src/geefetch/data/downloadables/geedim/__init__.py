import logging
from pathlib import Path
from typing import Any, List, Optional

import ee
from rasterio.crs import CRS
from rich.progress import Progress

from ..abc import DownloadableABC
from .download import BaseImage
from .enums import ExportType

log = logging.getLogger(__name__)


__all__ = ["BaseImage", "ExportableGeedimImage", "DownloadableGeedimImage"]


class ExportableGeedimImage(DownloadableABC):
    """Simple wrapper around `geedim.BaseImage` to adhere to the DownloadableABC interface."""

    def __init__(self, image: BaseImage):
        self.image = image

    def download(
        self,
        out: Path,
        region: ee.Geometry,
        crs: CRS,
        bands: List[str],
        scale: Optional[int] = None,
        dtype: str = "float32",
        **kwargs: Any,
    ) -> None:
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")
        self.image.export(
            out.name,
            ExportType.drive,
            wait=True,
            dtype=dtype,
            region=region,
            scale=scale,
            bands=bands,
            crs=f"EPSG:{crs.to_epsg()}",
        )


class DownloadableGeedimImage(DownloadableABC):
    """Simple wrapper around `geedim.BaseImage` to adhere to the DownloadableABC interface."""

    def __init__(self, image: BaseImage):
        self.image = image

    def download(
        self,
        out: Path,
        region: ee.Geometry,
        crs: CRS,
        bands: List[str],
        max_tile_size: Optional[int] = None,
        num_threads: Optional[int] = None,
        scale: Optional[int] = None,
        dtype: str = "float32",
        progress: Optional[Progress] = None,
        **kwargs: Any,
    ) -> None:
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")
        self.image.download(
            out,
            region=region,
            crs=f"EPSG:{crs.to_epsg()}",
            bands=bands,
            max_tile_size=max_tile_size,
            num_threads=num_threads,
            scale=scale,
            dtype=dtype,
            progress=progress,
        )
