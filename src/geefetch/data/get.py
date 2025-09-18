import logging
import math
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import shapely
from geobbox import GeoBoundingBox
from rasterio.crs import CRS
from retry import retry
from rich.progress import Progress

from ..utils.enums import CompositeMethod, DType, Format, P2Orbit, ResamplingMethod, S1Orbit
from ..utils.progress import default_bar
from ..utils.rasterio import create_vrt
from .downloadables import DownloadableABC
from .process import (
    geofile_is_clean,
    merge_tracked_geojson,
    merge_tracked_parquet,
    tif_is_clean,
    vector_is_clean,
)
from .satellites import (
    NASADEM,
    S1,
    S2,
    CustomSatellite,
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
    "download_custom",
    "download_dynworld",
    "download_gedi",
    "download_gedi_vector",
    "download_landsat8",
    "download_nasadem",
    "download_palsar2",
    "download_s1",
    "download_s2",
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
    selected_bands: list[str] | None = None,
    progress: Progress | None = None,
    **kwargs: Any,
) -> Path:
    """Download a specific chip of data from the satellite."""
    bands = selected_bands if selected_bands is not None else satellite.default_selected_bands
    satellite.check_selected_bands(bands)
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
    selected_bands: list[str] | None = None,
    check_clean: bool = True,
    **kwargs: Any,
) -> Path:
    """Download a specific chip of data from the satellite."""
    bands = selected_bands if selected_bands is not None else satellite.default_selected_bands
    if out.exists():
        log.debug(f"Found feature chip [cyan]{out}[/]")
        if not geofile_is_clean(out):
            log.info(f"File [cyan]{out}[/] is corrupted. Removing it.")
            out.unlink()
        else:
            log.debug(f"File {out} does not seem corrupted. Skipping download.")
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
    if satellite.is_raster and not tif_is_clean(out):
        if check_clean:
            log.error(f"Tif file {out} contains missing data.")
            raise BadDataError
        else:
            log.warning(f"Tif file {out} contains missing data")
    if satellite.is_vector and not vector_is_clean(out):
        if check_clean:
            log.error(f"Vector file {out} contains no data.")
            raise BadDataError
        else:
            log.warning(f"Vector file {out} contains no data.")
    return out


def download_time_series(
    data_dir: Path,
    bbox: GeoBoundingBox,
    satellite: SatelliteABC,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    satellite_get_kwargs: dict[str, Any] | None = None,
    satellite_download_kwargs: dict[str, Any] | None = None,
    check_clean: bool = True,
    filter_polygon: shapely.Geometry | None = None,
    tile_range: tuple[float, float] | None = None,
    **kwargs: Any,
) -> None:
    """Download time series of images from a specific satellite. Images are written in several .tif
    chips grouped in subdirectories in `dir`. Each subdirectory contains the time series of images
    of a single spatial tile.

    Parameters
    ----------
    data_dir : Path
        Directory or file name to write the downloaded files to. If a directory,
        the default `satellite` name is used as a base name.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    satellite : SatelliteABC
        The satellite which the images should originate from.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error.
        Defaults to 10 Mb.
    satellite_get_kwargs : dict[str, Any] | None
        Satellite-dependent parameters for getting data. Defaults to None.
    satellite_download_kwargs : dict[str, Any] | None
        Satellite-dependent parameters for downloading data. Defaults to None.
    check_clean : bool
        Whether to check if the data is clean. Defaults to True.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
                e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    **kwargs : Any
        Accepted but ignored additional arguments.
    """
    for kwarg in kwargs:
        log.warning(f"Argument {kwarg} is ignored.")
    if not data_dir.is_dir():
        raise ValueError(f"Invalid path {data_dir}. Expected an existing directory.")
    satellite_get_kwargs = satellite_get_kwargs if satellite_get_kwargs is not None else {}
    satellite_download_kwargs = (
        satellite_download_kwargs if satellite_download_kwargs is not None else {}
    )
    tiler = Tiler()
    tracker = TileTracker(satellite, data_dir)
    with default_bar() as progress:
        tiles = list(
            tiler.split(bbox, resolution * tile_shape, filter_polygon=filter_polygon, crs=crs)
        )
        if tile_range is not None:
            if not 0 <= tile_range[0] < tile_range[1] <= 1:
                raise ValueError(
                    f"Invalid tile range {tile_range}. Expected a range between 0. and 1."
                )
            start = math.floor(tile_range[0] * len(tiles))
            end = math.floor(tile_range[1] * len(tiles))
            log.info(f"Downloading tiles {start} to {end}")
            tiles = tiles[start:end]
        else:
            log.info("Downloading all tiles")
        overall_task = progress.add_task(
            f"[magenta]Downloading {satellite.full_name} chips...[/]",
            total=len(tiles),
        )

        for tile in tiles:
            data_get_kwargs = (
                dict(
                    aoi=tile,
                    start_date=start_date,
                    end_date=end_date,
                )
                | satellite_get_kwargs
            )
            tile_path = tracker.get_path(tile, format=satellite_download_kwargs.get("format", None))
            download_chip_ts(
                satellite.get_time_series,
                data_get_kwargs,
                tile,
                satellite,
                resolution,
                tile_path.with_name(tile_path.stem),
                progress=progress,
                selected_bands=selected_bands,
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
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    satellite_get_kwargs: dict[str, Any] | None = None,
    satellite_download_kwargs: dict[str, Any] | None = None,
    check_clean: bool = True,
    filter_polygon: shapely.Geometry | None = None,
    in_parallel: bool = False,
    max_workers: int = 1,
    tile_range: tuple[float, float] | None = None,
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
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
        Defaults to None.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error.
        Defaults to 10 Mb.
    satellite_get_kwargs : dict[str, Any] | None
        Satellite-dependent parameters for getting data. Defaults to None.
    satellite_download_kwargs : dict[str, Any] | None
        Satellite-dependent parameters for downloading data. Defaults to None.
    check_clean : bool
        Whether to check if the data is clean. Defaults to True.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    in_parallel : bool
        Whether to send parallel download requests. Do not use if the download backend
        is already threaded (e.g., :class:`geefetch.data.downloadable.geedim`). Defaults to False.
    max_workers : int
        How many parallel workers are used in case `in_parallel` is True. Defaults to 10.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    if not data_dir.is_dir():
        raise ValueError(f"Invalid path {data_dir}. Expected an existing directory.")
    satellite_get_kwargs = satellite_get_kwargs if satellite_get_kwargs is not None else {}
    satellite_download_kwargs = (
        satellite_download_kwargs if satellite_download_kwargs is not None else {}
    )
    tiler = Tiler()
    tracker = TileTracker(satellite, data_dir)
    with default_bar() as progress:
        tiles = list(
            tiler.split(bbox, resolution * tile_shape, filter_polygon=filter_polygon, crs=crs)
        )
        if tile_range is not None:
            if not 0 <= tile_range[0] < tile_range[1] <= 1:
                raise ValueError(
                    f"Invalid tile range {tile_range}. Expected a range between 0. and 1."
                )
            start = math.floor(tile_range[0] * len(tiles))
            end = math.floor(tile_range[1] * len(tiles))
            log.info(f"Downloading tiles {start} to {end}")
            tiles = tiles[start:end]
        else:
            log.info("Downloading all tiles")

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
                        selected_bands=selected_bands,
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
                        selected_bands=selected_bands,
                        max_tile_size=max_tile_size,
                        check_clean=check_clean,
                        **satellite_download_kwargs,
                    )
                    futures.append(future)
            if in_parallel:
                n_failures = 0
                try:
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            n_failures += 1
                            log.error(f"Download error: {e}")
                        finally:
                            progress.update(overall_task, advance=1)
                except KeyboardInterrupt:
                    executor.shutdown(wait=False, cancel_futures=True)
                    log.error(
                        "Keyboard interrupt. "
                        "Please wait while current download finish (up to a few minutes)."
                    )
                    raise
                if n_failures > 0:
                    raise DownloadError(f"Failed to download {n_failures} tiles.")
    if satellite.is_raster:
        _create_vrts(tracker)
    if satellite.is_vector and "format" in satellite_download_kwargs:
        match satellite_download_kwargs["format"]:
            case Format.PARQUET:
                merge_tracked_parquet(
                    TileTracker(satellite, data_dir, filter=lambda p: p.suffix == ".parquet")
                )
            case Format.GEOJSON:
                merge_tracked_geojson(
                    TileTracker(satellite, data_dir, filter=lambda p: p.suffix == ".geojson")
                )
            case _ as x:
                log.info(f"Don't know how to merge data of type {x}. Not merging.")

    log.info(
        f"[green]Finished[/] downloading {satellite.full_name} chips to [cyan]{tracker.root}[/]"
    )


def download_gedi(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download GEDI images fused as rasters. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `gedi.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    download_func = (
        download_time_series if composite_method == CompositeMethod.TIMESERIES else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=GEDIraster(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=1,
        check_clean=False,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )


def download_gedi_vector(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    tile_shape: int = 500,
    resolution: int = 10,
    filter_polygon: shapely.Geometry | None = None,
    format: Format = Format.CSV,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download GEDI vector points. Points are written in several .geojson files
    to `data_dir`.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    format : Format
        Format in which to save the vector points. Defaults to Format.CSV.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=GEDIvector(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        tile_shape=tile_shape,
        resolution=resolution,
        filter_polygon=filter_polygon,
        in_parallel=False,
        check_clean=False,
        satellite_download_kwargs={"format": format},
        tile_range=tile_range,
    )


def download_s1(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    orbit: S1Orbit = S1Orbit.ASCENDING,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download Sentinel-1 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `s1.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    orbit : S1Orbit
        The orbit used to filter Sentinel-1 images. Defaults to S1Orbit.ASCENDING.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    download_func = (
        download_time_series if (composite_method == CompositeMethod.TIMESERIES) else download
    )

    download_selected_bands: list[str] | None
    if orbit == S1Orbit.AS_BANDS and composite_method != CompositeMethod.TIMESERIES:
        selected_bands = (
            selected_bands if selected_bands is not None else S1().default_selected_bands
        )
        download_selected_bands = [
            *(f"{band}_ascending" for band in selected_bands),
            *(f"{band}_descending" for band in selected_bands),
        ]
    else:
        download_selected_bands = selected_bands
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=S1(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=download_selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        in_parallel=True,
        max_workers=1,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "orbit": orbit,
            "selected_bands": selected_bands,
            "resampling": resampling,
            "resolution": resolution,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )


def download_s2(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    cloudless_portion: int = 60,
    cloud_prb_thresh: int = 40,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download Sentinel-2 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `s2.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    cloudless_portion : int
        Portion of the image expected to be cloudless.
        See :meth:`geefetch.data.s2.get`. Defaults to 60.
    cloud_prb_thresh : int
        Cloud probability threshold. See :meth:`geefetch.data.s2.get`. Defaults to 40.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    download_func = (
        download_time_series if composite_method == CompositeMethod.TIMESERIES else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=S2(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=1,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "cloudless_portion": cloudless_portion,
            "cloud_prb_thresh": cloud_prb_thresh,
            "dtype": dtype,
            "resampling": resampling,
            "resolution": resolution,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )


def download_dynworld(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download Dynamic World images. Images are written in several .tif chips
    to `data_dir`. Additionnally a file `dynworld.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    download_func = (
        download_time_series if composite_method == CompositeMethod.TIMESERIES else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=DynWorld(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=1,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "resampling": resampling,
            "resolution": resolution,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )


def download_landsat8(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 30,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download Landsat 8 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `landsat8.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 30.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    download_func = (
        download_time_series if composite_method == CompositeMethod.TIMESERIES else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=Landsat8(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "resampling": resampling,
            "resolution": resolution,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )


def download_palsar2(
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 30,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    orbit: P2Orbit = P2Orbit.DESCENDING,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    refined_lee: bool = True,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download Palsar 2 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `palsar2.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 30.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    orbit : P2Orbit
        The orbit used to filter Palsar-2 images. Defaults to P2Orbit.ASCENDING.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    refined_lee : bool
        Whether to apply the Refined Lee filter to reduce speckle noise.
        Defaults to True.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    download_func = (
        download_time_series if composite_method == CompositeMethod.TIMESERIES else download
    )
    download_func(
        data_dir=data_dir,
        bbox=bbox,
        satellite=Palsar2(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "orbit": orbit,
            "resampling": resampling,
            "resolution": resolution,
            "refined_lee": refined_lee,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )


def download_nasadem(
    data_dir: Path,
    bbox: GeoBoundingBox,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Polygon | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download NASADEM images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `nasadem.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Polygon | None
        More fine-grained AOI than `bbox`. Defaults to None.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    if composite_method == CompositeMethod.TIMESERIES:
        raise ValueError("Time series is not relevant for DEM.")
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=NASADEM(),
        start_date=None,
        end_date=None,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=1,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "resampling": resampling,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )


def download_custom(
    satellite_custom: CustomSatellite,
    data_dir: Path,
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: int = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Polygon | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    tile_range: tuple[float, float] | None = None,
) -> None:
    """Download images from a custom data source. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `nasadem.vrt` is written to combine all the chips.

    Parameters
    ----------
    satellite_custom : CustomSatellite
    data_dir : Path
        Directory to write the downloaded files to.
    bbox : GeoBoundingBox
        The box defining the region of interest.
    start_date : str | None
        The start date of the time period of interest.
    end_date : str | None
        The end date of the time period of interest.
    selected_bands : list[str] | None
        The bands to download. If None, the default satellite bands are used.
    crs : CRS | None
        The CRS in which to download data. If None, AOI is split in UTM zones and
        data is downloaded in their local UTM zones. Defaults to None.
    resolution : int
        Resolution of the downloaded data, in meters. Defaults to 10.
    tile_shape : int
        Side length of a downloaded chip, in pixels. Defaults to 500.
    max_tile_size : int
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error. Defaults to 10.
    composite_method : CompositeMethod
        The composite method to mosaic the image collection. Can be CompositeMethod.TIMESERIES to
        download data as a time series instead of turning it into a mosaic.
        Defaults to CompositeMethod.MEDIAN.
    dtype : DType
        The data type of the downloaded images. Defaults to DType.Float32.
    filter_polygon : shapely.Polygon | None
        More fine-grained AOI than `bbox`. Defaults to None.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    tile_range: tuple[float, float] | None
        Start (inclusive) and end (exclusive) tile percentage to download,
        e.g. (0.5, 1.) will download the last half of all tiles.
        If None, all tiles are downloaded. Defaults to None.
    """
    if composite_method == CompositeMethod.TIMESERIES:
        raise ValueError("Time series is not relevant for Custom Satellites.")
    download(
        data_dir=data_dir,
        bbox=bbox,
        satellite=satellite_custom,
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        in_parallel=True,
        max_workers=1,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "resampling": resampling,
            "resolution": resolution,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        tile_range=tile_range,
    )
