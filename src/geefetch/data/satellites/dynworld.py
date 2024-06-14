import logging
from typing import Any

import ee

from ...utils.coords import WGS84, BoundingBox
from ...utils.gee import CompositeMethod, DType
from ..downloadables import DownloadableGeedimImage
from ..downloadables.geedim import BaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)


class DynWorldBase(SatelliteABC):
    _bands = [
        "water",
        "trees",
        "grass",
        "flooded_vegetation",
        "crops",
        "shrub_and_scrub",
        "built",
        "bare",
        "snow_and_ice",
        "label",
    ]
    _selected_bands = [
        "water",
        "trees",
        "grass",
        "flooded_vegetation",
        "crops",
        "shrub_and_scrub",
        "built",
        "bare",
        "snow_and_ice",
    ]

    @property
    def bands(self):
        return self._bands

    @property
    def selected_bands(self):
        return self._selected_bands

    @property
    def pixel_range(self):
        return 0, 1

    @property
    def resolution(self):
        return 10

    @property
    def is_raster(self) -> bool:
        return True

    def get_col(
        self,
        aoi: BoundingBox,
        start_date: str,
        end_date: str,
    ) -> ee.ImageCollection:
        """Get Dynamic World cloud free collection.

        Parameters
        ----------
        aoi : BoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        """
        bounds = aoi.transform(WGS84).to_ee_geometry()

        return (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
        )


class DynWorldGeedim(DynWorldBase):
    def get(
        self,
        aoi: BoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEDIAN,
        dtype: DType = DType.Float32,
        buffer: float = 100,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get Dynamic World cloud free collection.

        Parameters
        ----------
        aoi : BoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        composite_method: CompositeMethod
        buffer : float, optional
            Kernel size to dilate cloud/shadow patches.

        Returns
        -------
        dynworld_im : DownloadableGeedimImage
            A Dynamic World composite image of the specified AOI and time range,
            with clouds filtered out.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")
        bounds = aoi.transform(WGS84).to_ee_geometry()
        dynworld_col = self.get_col(
            aoi,
            start_date,
            end_date,
        )
        min_p, max_p = self.pixel_range
        dynworld_im = (
            composite_method.transform(dynworld_col).clip(bounds).clamp(min_p, max_p)
        )
        match dtype:
            case DType.Float64:
                dynworld_im = dynworld_im.toUint64()
            case DType.Float32:
                pass
            case DType.UInt16:
                dynworld_im = (
                    dynworld_im.add(-min_p)
                    .multiply((2**16 - 1) / (max_p - min_p))
                    .toUint16()
                )
            case DType.UInt8:
                dynworld_im = (
                    dynworld_im.add(-min_p)
                    .multiply((2**8 - 1) / (max_p - min_p))
                    .toUint8()
                )
            case _:
                raise ValueError(f"Unsupported {dtype=}.")
        dynworld_im = BaseImage(dynworld_im)
        n_images = len(dynworld_col.getInfo()["features"])
        if n_images > 500:
            log.warn(
                f"Dynamic World mosaicking with a large amount of images (n={n_images}). Expect slower download time."
            )
        log.debug(f"Dynamic World mosaicking with {n_images} images.")
        return DownloadableGeedimImage(dynworld_im)

    @property
    def name(self) -> str:
        return "dyn_world"

    @property
    def full_name(self) -> str:
        return "Dynamic World (Geedim)"


dynworld = DynWorldGeedim()
