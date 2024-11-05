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

__all__ = ["S1"]


class S1(SatelliteABC):
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

    def get_col(
        self, aoi: GeoBoundingBox, start_date: str, end_date: str
    ) -> ee.ImageCollection:
        """Get Sentinel-1 collection.

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
        s1_col : ee.ImageCollection
            A Sentinel-1 collection of the specified AOI and time range.
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()
        return (  # type: ignore[no-any-return]
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING"))
            .select(self.selected_bands)
        )

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get Sentinel-1 collection.

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
        s1_im: DownloadableGeedimImageCollection
            A Sentinel-1 time series collection of the specified AOI and time range.
        """
        s1_col = self.get_col(aoi, start_date, end_date)

        images = {}
        info = s1_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(
                f"Found 0 Sentinel-1 image." f"Check region {aoi.transform(WGS84)}."
            )
            raise RuntimeError("Collection of 0 Sentinel-1 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            if Polygon(
                PatchedBaseImage.from_id(id_).footprint["coordinates"][0]
            ).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = ee.Image(id_)
                im = self.convert_image(im, dtype)
                images[id_.removeprefix("COPERNICUS/S1_GRD/")] = PatchedBaseImage(im)
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
        """Get Sentinel-1 collection.

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
        s1_im: DownloadableGeedimImage
            A Sentinel-1 composite image of the specified AOI and time range.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")

        bounds = aoi.transform(WGS84).to_ee_geometry()
        s1_col = self.get_col(aoi, start_date, end_date)

        info = s1_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
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
        s1_im = PatchedBaseImage(s1_im)
        return DownloadableGeedimImage(s1_im)

    @property
    def name(self) -> str:
        return "s1"

    @property
    def full_name(self) -> str:
        return "Sentinel-1"
