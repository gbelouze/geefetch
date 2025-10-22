import logging
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import getpid
from pathlib import Path
from typing import Any, cast

import shapely
from geobbox import GeoBoundingBox
from rasterio.crs import CRS
from retry import retry

from ..cli.omegaconfig import SpeckleFilterConfig, TerrainNormalizationConfig
from ..utils.enums import (
    CompositeMethod,
    DType,
    Format,
    P2Orbit,
    ResamplingMethod,
    S1Orbit,
)
from ..utils.gee import auth
from ..utils.log_multiprocessing import (
    LogQueue,
    LogQueueConsumer,
    init_log_queue_for_children,
)
from ..utils.progress import default_bar
from ..utils.progress_multiprocessing import (
    ProgressProtocol,
    ProgressQueue,
    ProgressQueueConsumer,
    QueuedProgress,
)
from ..utils.rasterio import create_vrt
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


def auth_and_log(ee_project_id: str) -> None:
    auth(ee_project_id)

    # to make sure there are no race condition for the attribution of authentification id to
    # the processes, see how `auth_and_log` is called
    time.sleep(1)

    log.info(f"Process {getpid()} authentified with {ee_project_id}")


@retry(exceptions=DownloadError, tries=5)
def download_chip(
    satellite: SatelliteABC,
    data_get_kwargs: dict[Any, Any],
    bbox: GeoBoundingBox,
    scale: int,
    out: Path,
    selected_bands: list[str] | None = None,
    check_clean: bool = True,
    progress: ProgressProtocol | None = None,
    as_time_series: bool = False,
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
    data = (
        satellite.get(**data_get_kwargs)
        if not as_time_series
        else satellite.get_time_series(**data_get_kwargs)
    )

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
    if satellite.is_raster and check_clean and not tif_is_clean(out):
        log.error(f"Tif file {out} contains missing data.")
        raise BadDataError
    if satellite.is_vector and check_clean and not vector_is_clean(out):
        log.error(f"Vector file {out} contains no data.")
        raise BadDataError
    return out


def download(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    satellite: SatelliteABC,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    satellite_get_kwargs: dict[str, Any] | None = None,
    satellite_download_kwargs: dict[str, Any] | None = None,
    as_time_series: bool = False,
    check_clean: bool = True,
    filter_polygon: shapely.Geometry | None = None,
) -> None:
    """Download images from a specific satellite. Images are written in several .tif chips
    to `dir`. Additionally, a file `.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory or file name to write the downloaded files to. If a directory,
        the default `satellite` name is used as a base name.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
        Parameter adjusting the memory consumption in Google Earth Engine, in Mb.
        Choose the highest possible that doesn't raise a User Memory Excess error.
        Defaults to 10 Mb.
    satellite_get_kwargs : dict[str, Any] | None
        Satellite-dependent parameters for getting data. Defaults to None.
    satellite_download_kwargs : dict[str, Any] | None
        Satellite-dependent parameters for downloading data. Defaults to None.
    as_time_series : bool
        If True, data is downloaded as time series, if False, it is composited as a mosaic.
        Defaults to False.
    check_clean : bool
        Whether to check if the data is clean. Defaults to True.
    filter_polygon : shapely.Geometry | None
        More fine-grained AOI than `bbox`. Defaults to None.
    """
    if not data_dir.is_dir():
        raise ValueError(f"Invalid path {data_dir}. Expected an existing directory.")
    satellite_get_kwargs = satellite_get_kwargs if satellite_get_kwargs is not None else {}
    satellite_download_kwargs = (
        satellite_download_kwargs if satellite_download_kwargs is not None else {}
    )

    check_clean = check_clean and not as_time_series
    tiler = Tiler()
    tracker = TileTracker(satellite, data_dir)
    with default_bar() as progress:
        tiles = list(
            tiler.split(bbox, resolution * tile_shape, filter_polygon=filter_polygon, crs=crs)
        )
        log.info("Downloading all tiles")

        overall_task = progress.add_task(
            f"[magenta]Downloading {satellite.full_name} chips...[/]",
            total=len(tiles),
        )

        ee_project_ids = [ee_project_ids] if isinstance(ee_project_ids, str) else ee_project_ids
        max_workers = len(ee_project_ids)

        with mp.Manager() as manager:
            log_queue = cast(LogQueue, manager.Queue())
            progress_queue = cast(ProgressQueue, manager.Queue())
            progress_mp = QueuedProgress(progress_queue)
            with (
                LogQueueConsumer(log_queue),
                ProgressQueueConsumer(progress_queue, progress),
                ProcessPoolExecutor(
                    max_workers=max_workers,
                    initializer=init_log_queue_for_children,
                    initargs=(log_queue,),
                ) as executor,
            ):
                futures = []
                for ee_project_id, _ in zip(ee_project_ids, range(max_workers), strict=False):
                    # hacky authentification for the pool processes
                    executor.submit(auth_and_log, ee_project_id)
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
                    if as_time_series:
                        tile_path = tile_path.with_name(tile_path.stem)
                    future = executor.submit(
                        download_chip,
                        satellite,
                        data_get_kwargs,
                        tile,
                        resolution,
                        tile_path,
                        progress=progress_mp,
                        selected_bands=selected_bands,
                        max_tile_size=max_tile_size,
                        check_clean=check_clean,
                        as_time_series=as_time_series,
                        **satellite_download_kwargs,
                    )
                    futures.append(future)
                n_failures = 0
                try:
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            n_failures += 1
                            log.error(f"Download error: {e}")
                            raise
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
    if not as_time_series and satellite.is_raster:
        _create_vrts(tracker)
    if not as_time_series and satellite.is_vector and "format" in satellite_download_kwargs:
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
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
) -> None:
    """Download GEDI images fused as rasters. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `gedi.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    """
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
        bbox=bbox,
        satellite=GEDIraster(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        check_clean=False,
        filter_polygon=filter_polygon,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
        },
        as_time_series=(composite_method == CompositeMethod.TIMESERIES),
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_gedi_vector(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    tile_shape: int = 500,
    resolution: int = 10,
    filter_polygon: shapely.Geometry | None = None,
    format: Format = Format.CSV,
) -> None:
    """Download GEDI vector points. Points are written in several .geojson files
    to `data_dir`.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    """
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
        bbox=bbox,
        satellite=GEDIvector(),
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        tile_shape=tile_shape,
        resolution=resolution,
        filter_polygon=filter_polygon,
        check_clean=False,
        satellite_download_kwargs={"format": format},
    )


def download_s1(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    speckle_filter_config: SpeckleFilterConfig | None = None,
    terrain_normalization_config: TerrainNormalizationConfig | None = None,
    orbit: S1Orbit = S1Orbit.ASCENDING,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
) -> None:
    """Download Sentinel-1 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `s1.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    speckle_filter_config : SpeckleFilterConfig | None
        speckle_filtering configurations
    terrain_normalization_config: TerrainNormalizationConfig | None
        terrain_normalization configurations
    orbit : S1Orbit
        The orbit used to filter Sentinel-1 images. Defaults to S1Orbit.ASCENDING.
    resampling : ResamplingMethod
        The resampling method to use when reprojecting images.
        Can be BILINEAR, BICUBIC or NEAREST.
        Defaults to ResamplingMethod.BILINEAR.
    """

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
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
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
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "orbit": orbit,
            "selected_bands": selected_bands,
            "resampling": resampling,
            "resolution": resolution,
            "speckle_filter_config": speckle_filter_config,
            "terrain_normalization_config": terrain_normalization_config,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        as_time_series=(composite_method == CompositeMethod.TIMESERIES),
    )


def download_s2(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    cloudless_portion: int = 60,
    cloud_prb_thresh: int = 40,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
) -> None:
    """Download Sentinel-2 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `s2.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    """
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
        bbox=bbox,
        satellite=S2(),
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
            "cloudless_portion": cloudless_portion,
            "cloud_prb_thresh": cloud_prb_thresh,
            "dtype": dtype,
            "resampling": resampling,
            "resolution": resolution,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
        as_time_series=(composite_method == CompositeMethod.TIMESERIES),
    )


def download_dynworld(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
) -> None:
    """Download Dynamic World images. Images are written in several .tif chips
    to `data_dir`. Additionnally a file `dynworld.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    """
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
        bbox=bbox,
        satellite=DynWorld(),
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
        as_time_series=(composite_method == CompositeMethod.TIMESERIES),
    )


def download_landsat8(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 30,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
) -> None:
    """Download Landsat 8 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `landsat8.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    """
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
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
        as_time_series=(composite_method == CompositeMethod.TIMESERIES),
    )


def download_palsar2(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 30,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Geometry | None = None,
    orbit: P2Orbit = P2Orbit.DESCENDING,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
    refined_lee: bool = True,
) -> None:
    """Download Palsar 2 images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `palsar2.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    """
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
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
        as_time_series=(composite_method == CompositeMethod.TIMESERIES),
    )


def download_nasadem(
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: float = 5,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Polygon | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
) -> None:
    """Download NASADEM images. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `nasadem.vrt` is written to combine all the chips.

    Parameters
    ----------
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    """
    if composite_method == CompositeMethod.TIMESERIES:
        raise ValueError("Time series is not relevant for DEM.")
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
        bbox=bbox,
        satellite=NASADEM(),
        start_date=None,
        end_date=None,
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
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )


def download_custom(
    satellite_custom: CustomSatellite,
    data_dir: Path,
    ee_project_ids: str | list[str],
    bbox: GeoBoundingBox,
    start_date: str | None,
    end_date: str | None,
    selected_bands: list[str] | None = None,
    crs: CRS | None = None,
    resolution: int = 10,
    tile_shape: int = 500,
    max_tile_size: float = 10,
    composite_method: CompositeMethod = CompositeMethod.MEDIAN,
    dtype: DType = DType.Float32,
    filter_polygon: shapely.Polygon | None = None,
    resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
) -> None:
    """Download images from a custom data source. Images are written in several .tif chips
    to `data_dir`. Additionally, a file `nasadem.vrt` is written to combine all the chips.

    Parameters
    ----------
    satellite_custom : CustomSatellite
    data_dir : Path
        Directory to write the downloaded files to.
    ee_project_ids : str | list[str]
        One or more GEE project id for authentification. More than one id allows `geefetch`
        to process downloads in parallel.
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
    max_tile_size : float
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
    """
    if composite_method == CompositeMethod.TIMESERIES:
        raise ValueError("Time series is not implemented for Custom Satellites.")
    download(
        data_dir=data_dir,
        ee_project_ids=ee_project_ids,
        bbox=bbox,
        satellite=satellite_custom,
        start_date=start_date,
        end_date=end_date,
        selected_bands=selected_bands,
        crs=crs,
        resolution=resolution,
        tile_shape=tile_shape,
        max_tile_size=max_tile_size,
        filter_polygon=filter_polygon,
        check_clean=False,
        satellite_get_kwargs={
            "composite_method": composite_method,
            "dtype": dtype,
            "resampling": resampling,
            "resolution": resolution,
        },
        satellite_download_kwargs={"dtype": dtype.to_str()},
    )
