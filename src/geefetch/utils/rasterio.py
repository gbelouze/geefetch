import logging
from pathlib import Path
from typing import Iterable

from osgeo import gdal
from rasterio.crs import CRS

log = logging.getLogger(__name__)

__all__ = ["create_vrt", "WGS84"]

WGS84 = CRS.from_epsg(4326)


def create_vrt(out: Path, tifs: Iterable[Path]) -> None:
    """Create a .vrt for the given tif files."""
    gdal.DontUseExceptions()
    if out.suffix != ".vrt":
        raise ValueError(f"Expected a '.vrt' file but got {out}.")
    if out.exists():
        log.warn(f"Overwriting file {out}.")
        out.unlink()
    vrt = gdal.BuildVRT(str(out), [str(tif) for tif in tifs])
    vrt.FlushCache()
    log.debug(f"Created at .vrt composite at [cyan]{out}[/]")
