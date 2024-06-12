import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional

import shapely

from ..utils.coords import WGS84, BoundingBox
from ..utils.gee import CompositeMethod, DType, Format
from ..utils.progress import default_bar
from ..utils.rasterio import create_vrts
from .downloadables import DownloadableABC
from .process import tif_is_clean, vector_is_clean
from .satellites import SatelliteABC, dynworld, gedi_raster, gedi_vector, s1, s2
from .tiler import Tiler, TileTracker

log = logging.getLogger(__name__)


class UserMemoryLimitExceeded(Exception):
    pass


class DownloadError(Exception):
    pass


def download_chip(
    data_get_lazy: Callable[[Any, ...], DownloadableABC],
    data_get_kwargs: dict[Any],
    bbox: BoundingBox,
    satellite: SatelliteABC,
    scale: int,
    out: Path,
    check_clean: bool = True,
    **kwargs: Any,
) -> Path:
    bands = satellite.selected_bands
    if out.exists():
        log.debug(f"Found feature chip [cyan]{out}[/]. Skipping download.")
        return out
    data = data_get_lazy(**data_get_kwargs)

    data.download(
        out,
        crs=bbox.crs,
        region=bbox.transform(WGS84).to_ee_geometry(),
        bands=bands,
        scale=scale,
        **kwargs,
    )
    log.debug(f"Succesfully downloaded chip to [cyan]{out}[/]")
    if satellite.is_raster and check_clean and not tif_is_clean(out):
        log.error(f"Tif file {out} contains missing data.")
        raise DownloadError
    if satellite.is_vector and check_clean and not vector_is_clean(out):
        log.error(f"Geojson file {out} contains no data.")
        raise DownloadError
    return out


def download(
    data_dir: Path,
    bbox: BoundingBox,
    satellite: SatelliteABC,
    start_date: str,
    end_date: str,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    satellite_get_kwargs: Optional[dict[str, Any]] = None,
    satellite_download_kwargs: Optional[dict[str, Any]] = None,
    check_clean: bool = True,
    filter_polygon: Optional[shapely.Polygon] = None,
    in_parallel: bool = False,
) -> None:
    """Download images from a specific satellite. Images are written in several .tif chips
    to `dir`. Additionnally a file `.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory or file name to write the downloaded files to. If a directory,
        the default `satellite` name is used as a base name.
    bbox : BoundingBox
        The box defining the region of interest.
    satellite: SatelliteABC
        The satellite which the images should originate from.
    start_date, end_date: str
        The start and end of the time period of interest.
    composite_method: gd.CompositeMethod | str, optional
        The composite method to mosaic the image collection. Default is "median".
    resolution : int, optional
        Resolution of the downloaded data, in meter.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixel.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error.
        Default is 10 Mb.
    filter_polygon: shapely.Polygon, optional
        More fine grained AOI than `bbox`. See :meth:`Tiler.split`.
    in_parallel: bool
        Whether to send parallel download requests. Do not use if the download backend
        is aready threaded (e.g. ..class:`geefetch.data.downloadable.geedim`). Default is
        False.
    **kwargs
        Satellite-dependent parameters. See the corresponding `download_[satellite]`
        function help.
    """
    if not data_dir.is_dir():
        raise ValueError(f"Invalid path {data_dir}. Expected an existing directory.")
    satellite_get_kwargs = (
        satellite_get_kwargs if satellite_get_kwargs is not None else {}
    )
    satellite_download_kwargs = (
        satellite_download_kwargs if satellite_download_kwargs is not None else {}
    )
    tiler = Tiler()
    tracker = TileTracker(satellite, data_dir)
    with default_bar() as progress:
        tiles = list(
            tiler.split(bbox, resolution * tile_shape, filter_polygon=filter_polygon)
        )

        overall_task = progress.add_task(
            f"[magenta]Downloading {satellite.full_name} chips...[/]",
            total=len(tiles),
        )

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for tile in tiles:
                data_get_kwargs = (
                    dict(
                        aoi=tile.buffer(1_000), start_date=start_date, end_date=end_date
                    )
                    | satellite_get_kwargs
                )
                tile_path = tracker.get_path(
                    tile, format=satellite_download_kwargs.get("format", None)
                )
                if not in_parallel:
                    download_chip(
                        satellite.get,
                        data_get_kwargs,
                        tile,
                        satellite,
                        resolution,
                        tile_path,
                        progress=progress,
                        max_tile_size=max_tile_size,
                        check_clean=check_clean,
                        **satellite_download_kwargs,
                    )
                    progress.update(overall_task, advance=1)
                else:
                    future = executor.submit(
                        download_chip,
                        satellite.get,
                        data_get_kwargs,
                        tile,
                        satellite,
                        resolution,
                        tile_path,
                        max_tile_size=max_tile_size,
                        check_clean=check_clean,
                        **satellite_download_kwargs,
                    )
                    futures.append(future)
            if in_parallel:
                try:
                    for future in as_completed(futures):
                        progress.update(overall_task, advance=1)
                except KeyboardInterrupt:
                    executor.shutdown(wait=False, cancel_futures=True)
                    log.error(
                        "Keyboard interrupt. Please wait while current download finish (up to a few minutes)."
                    )
                    raise
        if satellite.is_raster:
            create_vrts(tracker)
    log.info(
        f"[green]Finished[/] downloading {satellite.full_name} chips to [cyan]{tracker.root}[/]"
    )


def download_gedi(
    data_dir: Path,
    bbox: BoundingBox,
    start_date: str,
    end_date: str,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    filter_polygon: Optional[shapely.Polygon] = None,
) -> None:
    """Download GEDI images fused as rasters. Images are written in several .tif chips
    to `data_dir`. Additionnally a file `gedi.vrt` is written to combine all the chips.

    Parameters
    ----------
    See :func:`download`.
    """
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=gedi_raster,
        start_date=start_date,
        end_date=end_date,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        check_clean=False,
        filter_polygon=filter_polygon,
    )


def download_gedi_vector(
    data_dir: Path,
    bbox: BoundingBox,
    start_date: str,
    end_date: str,
    tile_shape: int = 500,
    resolution: int = 10,
    filter_polygon: Optional[shapely.Polygon] = None,
    format: Format = Format.CSV,
) -> None:
    """Download GEDI vector points. Points are written in several .geojson files
    to `data_dir`.

    Parameters
    ----------
    See :func:`download`.
    """
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=gedi_vector,
        start_date=start_date,
        end_date=end_date,
        tile_shape=tile_shape,
        resolution=resolution,
        filter_polygon=filter_polygon,
        in_parallel=True,
        satellite_download_kwargs={"format": format},
    )


def download_s1(
    data_dir: Path,
    bbox: BoundingBox,
    start_date: str,
    end_date: str,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: Optional[shapely.Polygon] = None,
) -> None:
    """Download Sentinel-1 images. Images are written in several .tif chips
    to `data_dir`. Additionnally a file `s1.vrt` is written to combine all the chips.

    Parameters
    ----------
    See :func:`download`.
    """
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=s1,
        start_date=start_date,
        end_date=end_date,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={"composite_method": composite_method, "dtype": dtype},
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_s2(
    data_dir: Path,
    bbox: BoundingBox,
    start_date: str,
    end_date: str,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: Optional[shapely.Polygon] = None,
    cloudless_portion: int = 60,
    cloud_prb_thresh: int = 40,
) -> None:
    """Download Sentinel-2 images. Images are written in several .tif chips
    to `data_dir`. Additionnally a file `s2.vrt` is written to combine all the chips.

    Parameters
    ----------
    See :func:`download`.
    cloudless_portion: int, optional
        See :meth:`geefetch.data.s2.get`. Default is 60.
    cloud_prb_thresh: int, optional
        See :meth:`geefetch.data.s2.get`. Default is 40.
        Default is 40.
    """
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=s2,
        start_date=start_date,
        end_date=end_date,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "cloudless_portion": cloudless_portion,
            "cloud_prb_thresh": cloud_prb_thresh,
            "dtype": dtype,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_dynworld(
    data_dir: Path,
    bbox: BoundingBox,
    start_date: str,
    end_date: str,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    filter_polygon: Optional[shapely.Polygon] = None,
    cloudless_portion: int = 60,
) -> None:
    """Download Dynamic World images. Images are written in several .tif chips
    to `data_dir`. Additionnally a file `dynworld.vrt` is written to combine all the chips.

    Parameters
    ----------
    See :func:`download`.
    cloudless_portion: int, optional
        See :meth:`geefetch.data.dynworld.get`. Default is 60.
    """
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=dynworld,
        start_date=start_date,
        end_date=end_date,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
        },
    )
