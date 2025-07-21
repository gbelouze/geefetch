import logging
from collections.abc import Iterable
from pathlib import Path

from osgeo import gdal
from rasterio.crs import CRS

log = logging.getLogger(__name__)

__all__ = ["create_vrt", "WGS84"]

WGS84 = CRS.from_epsg(4326)


def create_vrt(out: Path, tifs: Iterable[Path]) -> None:
    """
    Create a GDAL Virtual Raster (VRT) file from a list of GeoTIFF files.

    Parameters
    ----------
    out : Path
        Path to the output `.vrt` file. Must have a `.vrt` suffix.
    tifs : Iterable[Path]
        List or iterable of input `.tif` files to be combined into the VRT.

    Raises
    ------
    ValueError
        If the output path does not have a `.vrt` suffix.
    """
    gdal.DontUseExceptions()
    if out.suffix != ".vrt":
        raise ValueError(f"Expected a '.vrt' file but got {out}.")
    if out.exists():
        log.warning(f"Overwriting file {out}.")
        out.unlink()
    vrt = gdal.BuildVRT(str(out), [str(tif) for tif in tifs])
    vrt.FlushCache()
    log.debug(f"Created at .vrt composite at [cyan]{out}[/]")
