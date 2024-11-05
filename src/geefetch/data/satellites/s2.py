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

__all__ = ["S2"]


class S2(SatelliteABC):
    _bands = [
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "B8",
        "B8A",
        "B9",
        "B11",
        "B12",
        "AOT",
        "WVP",
        "SCL",
        "TCI_R",
        "TCI_G",
        "TCI_B",
        "MSK_CLDPRB",
    ]
    _selected_bands = [
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "B8",
        "B8A",
        "B11",
        "B12",
    ]

    @property
    def bands(self):
        return self._bands

    @property
    def selected_bands(self):
        return self._selected_bands

    @property
    def pixel_range(self):
        return 0, 3000

    @property
    def resolution(self):
        return 10

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
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        cloudless_portion: int = 60,
        cloud_prb_thresh: int = 30,
    ) -> ee.ImageCollection:
        """Get Sentinel-2 cloud free collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        cloudless_portion : int, optional
            Threshold for the portion of filled pixels that must be cloud/shadow free (%).
            Images that do not fullfill the requirement are filtered out.
        cloud_prb_thresh : int, optional
            Threshold for cloud probability above which a pixel is filtered out (%).
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()

        s2_cloud = (
            ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
        )
        s2_col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
            .filter(
                f"CLOUDY_PIXEL_PERCENTAGE<={100-cloudless_portion} && "
                f"HIGH_PROBA_CLOUDS_PERCENTAGE<={(100-cloudless_portion)//2}"
            )
        )

        def mask_s2_clouds(im: ee.Image) -> ee.Image:
            qa = im.select("QA60")
            cloud_prb = ee.Image(im.get("s2cloudless")).select("probability")
            cloud_bit_mask = 1 << 10
            cirrus_bit_mask = 1 << 11
            mask = (
                (qa.bitwiseAnd(cloud_bit_mask).eq(0))
                .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
                .And(cloud_prb.lt(cloud_prb_thresh))
            )
            return im.updateMask(mask)

        s2_cloudless = ee.ImageCollection(
            ee.Join.saveFirst("s2cloudless").apply(
                primary=s2_col,
                secondary=s2_cloud,
                condition=ee.Filter.equals(
                    leftField="system:index", rightField="system:index"
                ),
            )
        ).map(mask_s2_clouds)

        return s2_cloudless  # type: ignore[no-any-return]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        cloudless_portion: int = 60,
        cloud_prb_thresh: int = 40,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get Sentinel-2 collection.

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
        s2_im: DownloadableGeedimImageCollection
            A Sentinel-2 time series collection of the specified AOI and time range.
        """
        for kwarg in kwargs:
            log.warn(f"Argument {kwarg} is ignored.")
        s2_cloudless = self.get_col(
            aoi,
            start_date,
            end_date,
            cloudless_portion=cloudless_portion,
            cloud_prb_thresh=cloud_prb_thresh,
        )

        images = {}
        info = s2_cloudless.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(
                f"Found 0 Sentinel-2 image." f"Check region {aoi.transform(WGS84)}."
            )
            raise RuntimeError("Collection of 0 Sentinel-2 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            if Polygon(
                PatchedBaseImage.from_id(id_).footprint["coordinates"][0]
            ).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = ee.Image(id_)
                im = self.convert_image(im, dtype)
                images[id_.removeprefix("COPERNICUS/S2_SR_HARMONIZED/")] = (
                    PatchedBaseImage(im)
                )
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEDIAN,
        dtype: DType = DType.Float32,
        cloudless_portion: int = 60,
        cloud_prb_thresh: int = 40,
        buffer: float = 100,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get Sentinel-2 cloud free collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        composite_method: CompositeMethod
        dtype: DType
            The data type for the image.
        cloudless_portion : int, optional
            Threshold for the portion of filled pixels that must be cloud/shadow free (%).
            Images that do not fullfill the requirement are filtered out.
        cloud_prb_thresh : int, optional
            Threshold for cloud probability above which a pixel is filtered out (%).
        buffer : float, optional
            Kernel size to dilate cloud/shadow patches.

        Returns
        -------
        s2_im : DownloadableGeedimImage
            A Sentinel-2 composite image of the specified AOI and time range,
            with clouds filtered out.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")
        bounds = aoi.transform(WGS84).to_ee_geometry()
        s2_cloudless = self.get_col(
            aoi,
            start_date,
            end_date,
            cloudless_portion=cloudless_portion,
            cloud_prb_thresh=cloud_prb_thresh,
        )
        min_p, max_p = self.pixel_range
        s2_im = composite_method.transform(s2_cloudless).clip(bounds)
        s2_im = self.convert_image(s2_im, dtype)
        s2_im = PatchedBaseImage(s2_im)
        n_images = len(s2_cloudless.getInfo()["features"])  # type: ignore[index]
        if n_images > 500:
            log.warn(
                f"Sentinel-2 mosaicking with a large amount of images (n={n_images}). Expect slower download time."
            )
            log.info("Change cloud masking parameters to lower the amount of images.")
        if n_images == 0:
            if cloudless_portion < 15:
                log.error(
                    f"Found 0 Sentinel-2 image for {cloudless_portion=} which is already conservative"
                    f"Check region {aoi.transform(WGS84)}"
                )
                raise RuntimeError("Collection of 0 Sentinel-2 image.")
            new_cloudless_portion = max(0, cloudless_portion - 10)
            log.warn(
                f"Found 0 Sentinel-2 image for {cloudless_portion=}."
                f"Trying new parameter cloudless_portion={new_cloudless_portion}"
            )
            return self.get(
                aoi,
                start_date,
                end_date,
                composite_method,
                dtype,
                new_cloudless_portion,
                cloud_prb_thresh,
                buffer,
            )
        log.debug(f"Sentinel-2 mosaicking with {n_images} images.")
        return DownloadableGeedimImage(s2_im)

    @property
    def name(self) -> str:
        return "s2"

    @property
    def full_name(self) -> str:
        return "Sentinel-2 (Geedim)"
