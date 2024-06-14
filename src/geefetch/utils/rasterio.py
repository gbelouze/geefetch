import logging
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from osgeo import gdal
from rasterio.io import DatasetReader

log = logging.getLogger(__name__)


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


def masked_array_from_dataset(dataset: DatasetReader) -> np.ndarray[Any, Any]:
    """Read the data content of a rasterio dataset, replacing the masked pixels with NaN values.

    Parameters
    ----------
    dataset : DatasetReader
        A rasterio dataset, e.g. one opened with `rasterio.open(file_path)`.
    """
    arr: np.ndarray[Any, Any] = dataset.read()
    if arr.dtype == np.uint16:
        arr = arr.astype(np.float32) / 2**15 - 1
    arr[dataset.read_masks() == 0] = None
    return arr
