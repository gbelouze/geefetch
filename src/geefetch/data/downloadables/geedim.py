import logging
from pathlib import Path
from typing import Any, List, Optional

import ee
from geedim.download import BaseImage
from geedim.enums import ExportType
from rasterio.crs import CRS
from rich.progress import Progress

from .abc import DownloadableABC

log = logging.getLogger(__name__)


__all__ = ["ExportableGeedimImage", "DownloadableGeedimImage"]


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


class DownloadableGeedimImageCollection(DownloadableABC):
    """Wrapper to download a collection of geedim images."""

    def __init__(self, id_to_images: List[BaseImage]):
        self.id_to_images = id_to_images

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
        if out.suffix != "":
            log.warn(f"Directory name for download has a suffix: {out.suffix}.")
        if not out.exists():
            out.mkdir()
        if not out.is_dir():
            raise ValueError(f"Path {out} was expected to be a directory.")
        task = progress.add_task(
            f"[magenta]Downloading time series to [cyan]{out}[/]",
            total=len(self.id_to_images),
        )
        for id_, image in self.id_to_images.items():
            dst_path = out / f"{id_}.tif"
            image.download(
                dst_path,
                region=region,
                crs=f"EPSG:{crs.to_epsg()}",
                bands=bands,
                max_tile_size=max_tile_size,
                num_threads=num_threads,
                scale=scale,
                dtype=dtype,
                progress=progress,
            )
            log.debug(f"Downloaded image to {dst_path}.")
            progress.advance(task)
