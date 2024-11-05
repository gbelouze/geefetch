import logging
from typing import Any

import ee
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import CompositeMethod, DType
from ...utils.rasterio import WGS84
from ..downloadables import DownloadableGeedimImage, DownloadableGeedimImageCollection
from ..downloadables.geedim import PatchedBaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["Palsar2"]


class Palsar2(SatelliteABC):
    _bands = [
        "HH",
        "HV",
        "LIN",
        "MSK",
    ]
    _selected_bands = [
        "HH",
        "HV",
    ]

    @property
    def bands(self):
        return self._bands

    @property
    def selected_bands(self):
        return self._selected_bands

    @property
    def pixel_range(self):
        return 0, 8000

    @property
    def resolution(self):
        return 25

    @property
    def is_raster(self) -> bool:
        return True

    def convert_image(self, im: ee.Image, dtype: DType) -> ee.Image:
        min_p, max_p = self.pixel_range
        im = im.clamp(min_p, max_p)
        match dtype:
            case DType.Float32:
                return im
            case DType.UInt16:
                return im.add(-min_p).multiply((2**16 - 1) / (max_p - min_p)).toUint16()
            case DType.UInt8:
                return im.add(-min_p).multiply((2**8 - 1) / (max_p - min_p)).toUint8()
            case _:
                raise ValueError(f"Unsupported {dtype=}.")

    def get_col(
        self, aoi: GeoBoundingBox, start_date: str, end_date: str
    ) -> ee.ImageCollection:
        """Get Palsar 2 collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()

        palsar2_col = (
            # ee.ImageCollection("JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR")  # very poor coverage
            ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH")  # yearly mosaics
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
        )

        return palsar2_col  # type: ignore[no-any-return]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get Palsar-2 collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.

        Returns
        -------
        p2_im: DownloadableGeedimImageCollection
            A Palsar-2 time series collection of the specified AOI and time range.
        """
        p2_col = self.get_col(aoi, start_date, end_date)

        images = {}
        info = p2_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(
                f"Found 0 Palsar-2 image." f"Check region {aoi.transform(WGS84)}."
            )
            raise RuntimeError("Collection of 0 Palsar-2 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            if Polygon(
                PatchedBaseImage.from_id(id_).footprint["coordinates"][0]
            ).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = ee.Image(id_)
                im = self.convert_image(im, dtype)
                images[id_.removeprefix("JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR")] = (
                    PatchedBaseImage(im)
                )
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEAN,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get Palsar-2 collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        composite_method: gd.CompositeMethod

        Returns
        -------
        p2_im: DownloadableGeedimImage
            A Palsar-2 composite image of the specified AOI and time range.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")

        bounds = aoi.transform(WGS84).to_ee_geometry()
        p2_col = self.get_col(aoi, start_date, end_date)

        info = p2_col.getInfo()
        n_images = len(info["features"])  # type: ignore
        if n_images > 500:
            log.warn(
                f"Palsar-2 mosaicking with a large amount of images (n={n_images}). Expect slower download time."
            )
        if n_images == 0:
            log.error(
                f"Found 0 Palsar-2 image." f"Check region {aoi.transform(WGS84)}."
            )
            raise RuntimeError("Collection of 0 Palsar-2 image.")

        log.debug(f"Palsar-2 mosaicking with {n_images} images.")
        p2_im = composite_method.transform(p2_col).clip(bounds)
        p2_im = self.convert_image(p2_im, dtype)
        p2_im = PatchedBaseImage(p2_im)
        return DownloadableGeedimImage(p2_im)

    @property
    def name(self) -> str:
        return "palsar2"

    @property
    def full_name(self) -> str:
        return "Palsar-2"
