import logging
from typing import Any

import ee
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import CompositeMethod, DType, S1Orbit
from ...utils.rasterio import WGS84
from ..downloadables import DownloadableGeedimImage, DownloadableGeedimImageCollection
from ..downloadables.geedim import PatchedBaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["S1"]


class S1(SatelliteABC):
    _bands = ["HH", "HV", "VV", "VH", "angle"]
    _default_selected_bands = ["VV", "VH"]

    @property
    def bands(self) -> list[str]:
        return self._bands

    @property
    def default_selected_bands(self) -> list[str]:
        return self._default_selected_bands

    @property
    def pixel_range(self):
        return -30, 0

    @property
    def is_raster(self):
        return True

    @property
    def resolution(self):
        return 10

    def get_col(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        orbit: S1Orbit = S1Orbit.ASCENDING,
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
        orbit : S1Orbit
            The orbit used to filter the collection.

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
            .filter(ee.Filter.eq("orbitProperties_pass", orbit.value))
        )

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        orbit: S1Orbit = S1Orbit.ASCENDING,
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
        dtype : DType
            The data type for the image
        orbit : S1Orbit
            The orbit used to filter the collection before mosaicking
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s1_im: DownloadableGeedimImageCollection
            A Sentinel-1 time series collection of the specified AOI and time range.
        """
        s1_col = self.get_col(aoi, start_date, end_date, orbit)

        images = {}
        info = s1_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(f"Found 0 Sentinel-1 image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Sentinel-1 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            if Polygon(PatchedBaseImage.from_id(id_).footprint["coordinates"][0]).intersects(
                aoi.to_shapely_polygon()
            ):
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
        orbit: S1Orbit = S1Orbit.ASCENDING,
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
        composite_method: CompositeMethod
            The method use to do mosaicking.
        dtype : DType
            The data type for the image
        orbit : S1Orbit
            The orbit used to filter the collection before mosaicking
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s1_im: DownloadableGeedimImage
            A Sentinel-1 composite image of the specified AOI and time range.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")

        s1_col = self.get_col(aoi, start_date, end_date, orbit)

        info = s1_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images > 500:
            log.warning(
                f"Sentinel-1 mosaicking with a large amount of images (n={n_images}). "
                "Expect slower download time."
            )
        if n_images == 0:
            log.error(f"Found 0 Sentinel-1 image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Sentinel-1 image.")

        log.debug(f"Sentinel-1 mosaicking with {n_images} images.")
        bounds = aoi.transform(WGS84).to_ee_geometry()
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
