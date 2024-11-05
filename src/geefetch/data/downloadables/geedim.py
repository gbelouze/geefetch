import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, List, Optional, Union

import ee
import geedim.utils
import numpy as np
import rasterio as rio
from geedim.download import BaseImage
from geedim.enums import ExportType
from geedim.tile import Tile
from geobbox import GeoBoundingBox
from rasterio.crs import CRS
from rich.progress import Progress
from shapely import Polygon

from ...utils.geedim import bounds_to_polygon, transform_polygon
from .abc import DownloadableABC

log = logging.getLogger(__name__)
geedim_log = logging.getLogger("patched_geedim")


__all__: list[str] = []


class PatchedBaseImage(BaseImage):
    def download(
        self,
        filename: Union[Path, str],
        overwrite: bool = False,
        num_threads: Optional[int] = None,
        max_tile_size: Optional[float] = None,
        max_tile_dim: Optional[int] = None,
        progress: Optional[Progress] = None,
        **kwargs,
    ):

        max_threads = num_threads or min(10, (os.cpu_count() or 1) + 4)
        geedim_log.debug(f"Using {max_threads} threads for download.")
        out_lock = threading.Lock()
        filename = Path(filename)
        if filename.exists():
            if overwrite:
                os.remove(filename)
            else:
                raise FileExistsError(f"{filename} exists")

        # prepare (resample, convert, reproject) the image for download
        exp_image, profile = self._prepare_for_download(**kwargs)

        # get the dimensions of an image tile that will satisfy GEE download limits
        tile_shape, num_tiles = exp_image._get_tile_shape(
            max_tile_size=max_tile_size, max_tile_dim=max_tile_dim
        )

        # find raw size of the download data (less than the actual download size as the image data is zipped in a
        # compressed geotiff)
        raw_download_size = exp_image.size
        if geedim_log.getEffectiveLevel() <= logging.DEBUG:
            dtype_size = np.dtype(exp_image.dtype).itemsize
            raw_tile_size = tile_shape[0] * tile_shape[1] * exp_image.count * dtype_size
            geedim_log.debug(f"{filename.name}:")
            geedim_log.debug(
                f"Uncompressed size: {PatchedBaseImage._str_format_size(raw_download_size)}"
            )
            geedim_log.debug(f"Num. tiles: {num_tiles}")
            geedim_log.debug(f"Tile shape: {tile_shape}")
            geedim_log.debug(
                f"Tile size: {PatchedBaseImage._str_format_size(int(raw_tile_size))}"
            )

        if raw_download_size > 1e9:
            # warn if the download is large (>1GB)
            geedim_log.warning(
                f"Consider adjusting `region`, `scale` and/or `dtype` to reduce the {filename.name}"
                f" download size (raw: {PatchedBaseImage._str_format_size(raw_download_size)})."
            )

        session = geedim.utils.retry_session(5)

        task = None
        if progress is not None:
            # configure the progress bar to monitor raw/uncompressed download size
            task = progress.add_task(
                f"[magenta]Downloading {filename.name}[/]",
                total=num_tiles,
            )
        with (
            rio.Env(GDAL_NUM_THREADS="ALL_CPUs", GTIFF_FORCE_RGBA=False),
            rio.open(filename, "w", **profile) as out_ds,
        ):

            def download_tile(tile: Tile):
                """Download a tile and write into the destination GeoTIFF."""
                tile_array = tile.download(session=session)
                with out_lock:
                    out_ds.write(tile_array, window=tile.window)

            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Run the tile downloads in a thread pool
                tiles = exp_image._tiles(tile_shape=tile_shape)
                futures = []
                if (
                    "coordinates" in self.footprint
                    and len(self.footprint["coordinates"]) > 0
                ):
                    if "crs" in self.footprint:
                        crs = geedim.utils.rio_crs(
                            self.footprint["crs"]["properties"]["name"]
                        )
                    else:
                        crs = CRS.from_epsg(4326)
                    im_bounds = transform_polygon(
                        Polygon(self.footprint["coordinates"][0]),
                        crs,
                        geedim.utils.rio_crs(exp_image.crs),
                    )
                else:
                    im_bounds = None
                keep_count, skip_count = 0, 0
                for tile in tiles:
                    tile_bounds = bounds_to_polygon(
                        *rio.windows.bounds(tile.window, exp_image.transform)
                    )
                    if im_bounds is None or tile_bounds.intersects(im_bounds):
                        futures.append(executor.submit(download_tile, tile))
                        keep_count += 1
                    else:
                        skip_count += 1
                geedim_log.debug(f"Skipped {skip_count} windows, kept {keep_count}.")
                try:
                    if progress is not None:
                        for completed_future in as_completed(futures):
                            n_finished = sum([future.done() for future in futures])
                            progress.update(
                                task, completed=n_finished, total=len(futures)
                            )
                            progress.refresh()
                            completed_future.result()
                        progress.update(task, visible=False)
                    else:
                        for completed_future in as_completed(futures):
                            completed_future.result()
                except KeyboardInterrupt:
                    geedim_log.error(
                        "Keyboard interrupt while downloading. "
                        "[red]Please wait[/] while current downloads finish (this may take up to a few minutes)."
                    )
                    executor.shutdown(wait=False, cancel_futures=True)
                    if filename.exists():
                        filename.unlink()
                    executor.shutdown(wait=True, cancel_futures=True)
                    raise
                except Exception as ex:
                    geedim_log.info(f"Exception: {str(ex)}\nCancelling...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    if filename.exists():
                        filename.unlink()
                    executor.shutdown(wait=True, cancel_futures=True)
                    raise ex

            # populate GeoTIFF metadata
            exp_image._write_metadata(out_ds)

        # build overviews
        exp_image._build_overviews(filename)


class ExportableGeedimImage(DownloadableABC):
    """Simple wrapper around `geedim.PatchedBaseImage` to adhere to the DownloadableABC interface."""

    def __init__(self, image: PatchedBaseImage):
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
    """Simple wrapper around `geedim.PatchedBaseImage` to adhere to the DownloadableABC interface."""

    def __init__(self, image: PatchedBaseImage):
        self.image = image

    def download(
        self,
        out: Path,
        region: GeoBoundingBox,
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
            region=region.to_ee_geometry(),
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

    def __init__(self, id_to_images: dict[str, PatchedBaseImage]):
        self.id_to_images = id_to_images

    def download(
        self,
        out: Path,
        region: GeoBoundingBox,
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
            if dst_path.exists():
                log.debug(f"Found existing {dst_path}. Skipping download.")
                continue
            image.download(
                dst_path,
                region=region.to_ee_geometry(),
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
