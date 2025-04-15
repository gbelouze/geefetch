import logging
from typing import Any

from ee.filter import Filter
from ee.image import Image
from ee.imagecollection import ImageCollection
from ee.join import Join
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import CompositeMethod, DType, ResamplingMethod
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
    _default_selected_bands = [
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
    def bands(self) -> list[str]:
        return self._bands

    @property
    def default_selected_bands(self) -> list[str]:
        return self._default_selected_bands

    @property
    def pixel_range(self):
        return 0, 3000

    @property
    def resolution(self):
        return 10

    @property
    def is_raster(self) -> bool:
        return True

    def get_col(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        cloudless_portion: int = 60,
        cloud_prb_thresh: int = 30,
    ) -> ImageCollection:
        """Get Sentinel-2 cloud free collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        cloudless_portion : int
            Threshold for the portion of filled pixels that must be cloud/shadow free (%).
            Images that do not fullfill the requirement are filtered out. Defaults to 60.
        cloud_prb_thresh : int
            Threshold for cloud probability above which a pixel is filtered out (%).
            Defaults to 30.

        Returns
        -------
        s2_cloudless : ImageCollection
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()

        s2_cloud = (
            ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
        )
        s2_col = (
            ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
            .filter(
                f"CLOUDY_PIXEL_PERCENTAGE<={100 - cloudless_portion} && "
                f"HIGH_PROBA_CLOUDS_PERCENTAGE<={(100 - cloudless_portion) // 2}"
            )
        )

        def mask_s2_clouds(im: Image) -> Image:
            qa = im.select("QA60")
            cloud_prb = Image(im.get("s2cloudless")).select("probability")
            cloud_bit_mask = 1 << 10
            cirrus_bit_mask = 1 << 11
            mask = (
                (qa.bitwiseAnd(cloud_bit_mask).eq(0))
                .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
                .And(cloud_prb.lt(cloud_prb_thresh))
            )
            return im.updateMask(mask)

        s2_cloudless = ImageCollection(
            Join.saveFirst("s2cloudless").apply(
                primary=s2_col,
                secondary=s2_cloud,
                condition=Filter.equals(leftField="system:index", rightField="system:index"),
            )
        ).map(mask_s2_clouds)

        return s2_cloudless  # type: ignore[no-any-return]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
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
        dtype: DType
            The data type for the image.
        resampling : ResamplingMethod
            The resampling method to use when processing the image.
        cloudless_portion : int
            Threshold for the portion of filled pixels that must be cloud/shadow free (%).
            Images that do not fullfill the requirement are filtered out.
        cloud_prb_thresh : int
            Threshold for cloud probability above which a pixel is filtered out (%).
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s2_im: DownloadableGeedimImageCollection
            A Sentinel-2 time series collection of the specified AOI and time range.
        """
        for kwarg in kwargs:
            log.warning(f"Argument {kwarg} is ignored.")
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
            log.error(f"Found 0 Sentinel-2 image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Sentinel-2 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            footprint = PatchedBaseImage.from_id(id_).footprint
            assert footprint is not None
            if Polygon(footprint["coordinates"][0]).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = Image(id_)
                # resample
                if resampling.value is not None:
                    im = im.resample(resampling.value)
                # apply dtype
                im = self.convert_dtype(im, dtype)
                images[id_.removeprefix("COPERNICUS/S2_SR_HARMONIZED/")] = PatchedBaseImage(im)
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEDIAN,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
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
            The method to use for compositing.
        dtype: DType
            The data type for the image.
        resampling : ResamplingMethod
            The resampling method to use when processing the image.
        cloudless_portion : int
            Threshold for the portion of filled pixels that must be cloud/shadow free (%).
            Images that do not fullfill the requirement are filtered out.
        cloud_prb_thresh : int
            Threshold for cloud probability above which a pixel is filtered out (%).
        buffer : float
            Kernel size to dilate cloud/shadow patches.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s2_im : DownloadableGeedimImage
            A Sentinel-2 composite image of the specified AOI and time range,
            with clouds filtered out.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")
        bounds = aoi.transform(WGS84).to_ee_geometry()
        s2_cloudless = self.get_col(
            aoi,
            start_date,
            end_date,
            cloudless_portion=cloudless_portion,
            cloud_prb_thresh=cloud_prb_thresh,
        )
        # Apply resampling
        if resampling.value is not None:
            s2_cloudless = s2_cloudless.map(lambda img: img.resample(resampling.value))
        s2_im = composite_method.transform(s2_cloudless).clip(bounds)
        # Apply dtype
        s2_im = self.convert_dtype(s2_im, dtype)
        s2_im = PatchedBaseImage(s2_im)
        n_images = len(s2_cloudless.getInfo()["features"])  # type: ignore[index]
        if n_images > 500:
            log.warning(
                f"Sentinel-2 mosaicking with a large amount of images (n={n_images}). "
                "Expect slower download time."
            )
            log.info("Change cloud masking parameters to lower the amount of images.")
        if n_images == 0:
            if cloudless_portion < 15:
                log.error(
                    f"Found 0 Sentinel-2 image for {cloudless_portion=} "
                    "which is already conservative. "
                    f"Check region {aoi.transform(WGS84)}"
                )
                raise RuntimeError("Collection of 0 Sentinel-2 image.")
            new_cloudless_portion = max(0, cloudless_portion - 10)
            log.warning(
                f"Found 0 Sentinel-2 image for {cloudless_portion=}."
                f"Trying new parameter cloudless_portion={new_cloudless_portion}"
            )
            return self.get(
                aoi=aoi,
                start_date=start_date,
                end_date=end_date,
                composite_method=composite_method,
                dtype=dtype,
                cloudless_portion=new_cloudless_portion,
                cloud_prb_thresh=cloud_prb_thresh,
                buffer=buffer,
                resampling=resampling,
            )
        log.debug(f"Sentinel-2 mosaicking with {n_images} images.")
        return DownloadableGeedimImage(s2_im)

    @property
    def name(self) -> str:
        return "s2"

    @property
    def full_name(self) -> str:
        return "Sentinel-2 (Geedim)"
