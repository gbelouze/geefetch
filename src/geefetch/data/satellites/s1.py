import logging
from typing import Any

import ee

from ...utils.coords import WGS84, BoundingBox
from ...utils.gee import CompositeMethod, DType
from ..downloadables import (
    DownloadableGeedimImage,
    DownloadableGeedimImageCollection,
    DownloadableGEEImage,
)
from ..downloadables.geedim import BaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)


class S1Base(SatelliteABC):
    _bands = ["HH", "HV", "VV", "VH", "angle"]
    _selected_bands = ["VV", "VH"]

    @property
    def bands(self):
        return self._bands

    @property
    def selected_bands(self):
        return self._selected_bands

    @property
    def pixel_range(self):
        return -30, 0

    @property
    def is_raster(self):
        return True

    @property
    def resolution(self):
        return 10

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

    def get_col(self, aoi: BoundingBox, start_date: str, end_date: str):
        """Get Sentinel-1 collection.

        Parameters
        ----------
        aoi : BoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.

        Returns
        -------
        s1_col : ee.ImageCollection
            A Sentinel-1 collection of the specified AOI and time range.
        """
        bounds = aoi.transform(WGS84).to_ee_geometry()
        return (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .select(self.selected_bands)
        )


class S1GEE(S1Base):
    def get(
        self,
        aoi: BoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEAN,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGEEImage:
        """Get Sentinel-1 collection.

        Parameters
        ----------
        aoi : BoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        composite_method: CompositeMethod

        Returns
        -------
        s1_im : gd.MaskedImage
            A Sentinel-1 composite image of the specified AOI and time range.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")
        bounds = aoi.transform(WGS84).to_ee_geometry()
        s1_col = self.get_col(aoi, start_date, end_date)
        s1_im = composite_method.transform(s1_col).clip(bounds)
        s1_im = self.convert_image(s1_im, dtype)
        return DownloadableGEEImage(s1_im)

    @property
    def name(self) -> str:
        return "s1gee"

    @property
    def full_name(self) -> str:
        return "Sentinel-1 (GEE)"


class S1Geedim(S1Base):
    def get_time_series(
        self,
        aoi: BoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get Sentinel-1 collection.

        Parameters
        ----------
        aoi : BoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.

        Returns
        -------
        s1_im: DownloadableGeedimImageCollection
            A Sentinel-1 time series collection of the specified AOI and time range.
        """
        bounds = aoi.transform(WGS84).to_ee_geometry()
        s1_col = self.get_col(aoi, start_date, end_date)

        images = {}
        info = s1_col.getInfo()
        n_images = len(info["features"])
        if n_images == 0:
            log.error(
                f"Found 0 Sentinel-1 image." f"Check region {aoi.transform(WGS84)}."
            )
            raise RuntimeError("Collection of 0 Sentinel-1 image.")
        for feature in info["features"]:
            id_ = feature["id"]
            im = ee.Image(id_).clip(bounds)
            im = self.convert_image(im, dtype)
            images[id_.removeprefix("COPERNICUS/S1_GRD/")] = BaseImage(im)
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: BoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEAN,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get Sentinel-1 collection.

        Parameters
        ----------
        aoi : BoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        composite_method: gd.CompositeMethod

        Returns
        -------
        s1_im: DownloadableGeedimImage
            A Sentinel-1 composite image of the specified AOI and time range.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")

        bounds = aoi.transform(WGS84).to_ee_geometry()
        s1_col = self.get_col(aoi, start_date, end_date)

        info = s1_col.getInfo()
        n_images = len(info["features"])
        if n_images > 500:
            log.warn(
                f"Sentinel-1 mosaicking with a large amount of images (n={n_images}). Expect slower download time."
            )
        if n_images == 0:
            log.error(
                f"Found 0 Sentinel-1 image." f"Check region {aoi.transform(WGS84)}."
            )
            raise RuntimeError("Collection of 0 Sentinel-1 image.")

        log.debug(f"Sentinel-1 mosaicking with {n_images} images.")
        s1_im = composite_method.transform(s1_col).clip(bounds)
        s1_im = self.convert_image(s1_im, dtype)
        s1_im = BaseImage(s1_im)
        return DownloadableGeedimImage(s1_im)

    @property
    def name(self) -> str:
        return "s1"

    @property
    def full_name(self) -> str:
        return "Sentinel-1"


s1gee = S1GEE()
s1 = S1Geedim()
