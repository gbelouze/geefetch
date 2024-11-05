import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional

import shapely
from geobbox import GeoBoundingBox
from rasterio.crs import CRS
from retry import retry
from rich.progress import Progress

from ..utils.enums import CompositeMethod, DType, Format
from ..utils.progress import default_bar
from ..utils.rasterio import create_vrt
from .downloadables import DownloadableABC
from .process import (
    merge_tracked_geojson,
    merge_tracked_parquet,
    tif_is_clean,
    vector_is_clean,
)
from .satellites import (
    S1,
    S2,
    DynWorld,
    GEDIraster,
    GEDIvector,
    Landsat8,
    Palsar2,
    SatelliteABC,
)
from .tiler import Tiler, TileTracker

log = logging.getLogger(__name__)

__all__ = [
    "UserMemoryLimitExceeded",
    "DownloadError",
    "BadDataError",
    "download_s1",
    "download_s2",
    "download_dynworld",
    "download_gedi",
    "download_gedi_vector",
]


def _create_vrts(tracker: TileTracker) -> None:
    """Create .vrt files for the tracked tif files."""
    crs_to_paths = tracker.crs_to_paths()
    for crs, paths in crs_to_paths.items():
        out = tracker.root / f"{tracker.satellite.name}_{tracker.name_crs(crs)}.vrt"
        create_vrt(out, paths)


class UserMemoryLimitExceeded(Exception):
    pass


class DownloadError(Exception):
    pass


class BadDataError(Exception):
    pass


# @retry(exceptions=DownloadError, tries=5)
def download_chip_ts(
    data_get_lazy: Callable[..., DownloadableABC],
    data_get_kwargs: dict[Any, Any],
    bbox: GeoBoundingBox,
    satellite: SatelliteABC,
    scale: int,
    out: Path,
    progress: Optional[Progress] = None,
    **kwargs: Any,
) -> Path:
    """Download a specific chip of data from the satellite."""
    bands = satellite.selected_bands
    data = data_get_lazy(**data_get_kwargs)

    try:
        data.download(
            out,
            crs=bbox.crs,
            region=bbox,
            bands=bands,
            scale=scale,
            progress=progress,
            **kwargs,
        )
        log.debug(f"Succesfully downloaded chip to [cyan]{out}[/]")
    except Exception as e:
        log.error(f"Failed to download chip to {out}: {e}")
        raise DownloadError from e
    return out


@retry(exceptions=DownloadError, tries=5)
def download_chip(
    data_get_lazy: Callable[..., DownloadableABC],
    data_get_kwargs: dict[Any, Any],
    bbox: GeoBoundingBox,
    satellite: SatelliteABC,
    scale: int,
    out: Path,
    check_clean: bool = True,
    **kwargs: Any,
) -> Path:
    """Download a specific chip of data from the satellite."""
    bands = satellite.selected_bands
    if out.exists():
        log.debug(f"Found feature chip [cyan]{out}[/]. Skipping download.")
        return out
    data = data_get_lazy(**data_get_kwargs)

    try:
        data.download(
            out,
            crs=bbox.crs,
            region=bbox,
            bands=bands,
            scale=scale,
            **kwargs,
        )
        log.debug(f"Succesfully downloaded chip to [cyan]{out}[/]")
    except Exception as e:
        log.error(f"Failed to download chip to {out}: {e}")
        raise DownloadError from e
    if satellite.is_raster and check_clean and not tif_is_clean(out):
        log.error(f"Tif file {out} contains missing data.")
        raise BadDataError
    if satellite.is_vector and check_clean and not vector_is_clean(out):
        log.error(f"Geojson file {out} contains no data.")
        raise BadDataError
    return out


def download_time_series(
    data_dir: Path,
    bbox: GeoBoundingBox,
    satellite: SatelliteABC,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    satellite_get_kwargs: Optional[dict[str, Any]] = None,
    satellite_download_kwargs: Optional[dict[str, Any]] = None,
    check_clean: bool = True,
    filter_polygon: Optional[shapely.Polygon] = None,
    **kwargs: Any,
) -> None:
    """Download images from a specific satellite. Images are written in several .tif chips
    to `dir`. Additionally, a file `.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory or file name to write the downloaded files to. If a directory,
        the default `satellite` name is used as a base name.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    satellite : SatelliteABC
        The satellite which the images should originate from.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error.
        Defaults to 10 Mb.
    satellite_get_kwargs : Optional[dict[str, Any]], optional
        Satellite-dependent parameters for getting data. Defaults to None.
    satellite_download_kwargs : Optional[dict[str, Any]], optional
        Satellite-dependent parameters for downloading data. Defaults to None.
    check_clean : bool, optional
        Whether to check if the data is clean. Defaults to True.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    """
    for kwarg in kwargs:
        log.warn(f"Argument {kwarg} is ignored.")
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
            tiler.split(
                bbox, resolution * tile_shape, filter_polygon=filter_polygon, crs=crs
            )
        )

        overall_task = progress.add_task(
            f"[magenta]Downloading {satellite.full_name} chips...[/]",
            total=len(tiles),
        )

        for tile in tiles:
            data_get_kwargs = (
                dict(aoi=tile, start_date=start_date, end_date=end_date)
                | satellite_get_kwargs
            )
            tile_path = tracker.get_path(
                tile, format=satellite_download_kwargs.get("format", None)
            )
            download_chip_ts(
                satellite.get_time_series,
                data_get_kwargs,
                tile,
                satellite,
                resolution,
                tile_path.with_name(tile_path.stem),
                progress=progress,
                max_tile_size=max_tile_size,
                **satellite_download_kwargs,
            )
            progress.update(overall_task, advance=1)
        if satellite.is_raster:
            _create_vrts(tracker)
    log.info(
        f"[green]Finished[/] downloading {satellite.full_name} chips to [cyan]{tracker.root}[/]"
    )


def download(
    data_dir: Path,
    bbox: GeoBoundingBox,
    satellite: SatelliteABC,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    satellite_get_kwargs: Optional[dict[str, Any]] = None,
    satellite_download_kwargs: Optional[dict[str, Any]] = None,
    check_clean: bool = True,
    filter_polygon: Optional[shapely.Polygon] = None,
    in_parallel: bool = False,
    max_workers: int = 10,
) -> None:
    """Download images from a specific satellite. Images are written in several .tif chips
    to `dir`. Additionally, a file `.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory or file name to write the downloaded files to. If a directory,
        the default `satellite` name is used as a base name.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    satellite : SatelliteABC
        The satellite which the images should originate from.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error.
        Defaults to 10 Mb.
    satellite_get_kwargs : Optional[dict[str, Any]], optional
        Satellite-dependent parameters for getting data. Defaults to None.
    satellite_download_kwargs : Optional[dict[str, Any]], optional
        Satellite-dependent parameters for downloading data. Defaults to None.
    check_clean : bool, optional
        Whether to check if the data is clean. Defaults to True.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    in_parallel : bool, optional
        Whether to send parallel download requests. Do not use if the download backend
        is already threaded (e.g., :class:`geefetch.data.downloadable.geedim`). Defaults to False.
    max_workers : int, optional
        How many parallel workers are used in case `in_parallel` is True. Defaults to 10.
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
            tiler.split(
                bbox, resolution * tile_shape, filter_polygon=filter_polygon, crs=crs
            )
        )

        overall_task = progress.add_task(
            f"[magenta]Downloading {satellite.full_name} chips...[/]",
            total=len(tiles),
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for tile in tiles:
                data_get_kwargs = (
                    dict(
                        aoi=tile,
                        start_date=start_date,
                        end_date=end_date,
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
                        progress=progress,
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
        _create_vrts(tracker)
    if satellite.is_vector and "format" in satellite_download_kwargs:
        match satellite_download_kwargs["format"]:
            case Format.PARQUET:
                merge_tracked_parquet(
                    TileTracker(
                        satellite, data_dir, filter=lambda p: p.suffix == ".parquet"
                    )
                )
            case Format.GEOJSON:
                merge_tracked_geojson(
                    TileTracker(
                        satellite, data_dir, filter=lambda p: p.suffix == ".geojson"
                    )
                )
            case _ as x:
                log.info(f"Don't know how to merge data of type {x}. Not merging.")

    log.info(
        f"[green]Finished[/] downloading {satellite.full_name} chips to [cyan]{tracker.root}[/]"
    )


def download_gedi(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: Optional[shapely.Polygon] = None,
) -> None:
    """Download GEDI images fused as rasters. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `gedi.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod, optional
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType, optional
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    """
    download_func = (
        download_time_series
        if composite_method == CompositeMethod.TIMESERIES
        else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=GEDIraster(),
        start_date=start_date,
        end_date=end_date,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=3,
        check_clean=False,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_gedi_vector(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    tile_shape: int = 500,
    resolution: int = 10,
    filter_polygon: Optional[shapely.Polygon] = None,
    format: Format = Format.CSV,
) -> None:
    """Download GEDI vector points. Points are written in several .geojson files
    to `data_dir`.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 10.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    format : Format, optional
        Format in which to save the vector points. Defaults to Format.CSV.
    """
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=GEDIvector(),
        start_date=start_date,
        end_date=end_date,
        crs=crs,
        tile_shape=tile_shape,
        resolution=resolution,
        filter_polygon=filter_polygon,
        in_parallel=True,
        satellite_download_kwargs={"format": format},
    )


def download_s1(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: Optional[shapely.Polygon] = None,
) -> None:
    """Download Sentinel-1 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `s1.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod, optional
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType, optional
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    """
    download_func = (
        download_time_series
        if (composite_method == CompositeMethod.TIMESERIES)
        else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=S1(),
        start_date=start_date,
        end_date=end_date,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        in_parallel=True,
        max_workers=3,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_s2(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
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
    to `data_dir`. Additionally, a file `s2.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod, optional
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType, optional
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    cloudless_portion : int, optional
        Portion of the image expected to be cloudless.
        See :meth:`geefetch.data.s2.get`. Defaults to 60.
    cloud_prb_thresh : int, optional
        Cloud probability threshold. See :meth:`geefetch.data.s2.get`. Defaults to 40.
    """
    download_func = (
        download_time_series
        if composite_method == CompositeMethod.TIMESERIES
        else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=S2(),
        start_date=start_date,
        end_date=end_date,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=3,
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
    bbox: GeoBoundingBox,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: Optional[shapely.Polygon] = None,
) -> None:
    """Download Dynamic World images. Images are written in several .tif chips
    to `data_dir`. Additionnally a file `dynworld.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod, optional
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType, optional
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    """
    download_func = (
        download_time_series
        if composite_method == CompositeMethod.TIMESERIES
        else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=DynWorld(),
        start_date=start_date,
        end_date=end_date,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=3,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_landsat8(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    resolution: int = 30,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: Optional[shapely.Polygon] = None,
) -> None:
    """Download Landsat 8 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `landsat8.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 30.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod, optional
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType, optional
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    """
    download_func = (
        download_time_series
        if composite_method == CompositeMethod.TIMESERIES
        else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=Landsat8(),
        start_date=start_date,
        end_date=end_date,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_palsar2(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str,
    end_date: str,
    crs: Optional[CRS] = None,
    resolution: int = 30,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: Optional[shapely.Polygon] = None,
) -> None:
    """Download Palsar 2 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `palsar2.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str
        The start date of the time period of interest.
    end_date : str
        The end date of the time period of interest.
    crs : Optional[CRS], optional
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int, optional
        Resolution of the downloaded data, in meters. Defaults to 30.
    tile_shape : int, optional
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int, optional
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod, optional
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType, optional
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : Optional[shapely.Polygon], optional
        More fine-grained AOI than `bbox`. Defaults to None.
    """
    download_func = (
        download_time_series
        if composite_method == CompositeMethod.TIMESERIES
        else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=Palsar2(),
        start_date=start_date,
        end_date=end_date,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )
