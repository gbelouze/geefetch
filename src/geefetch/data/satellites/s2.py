import logging
from typing import Any

from ee.ee_list import List
from ee.ee_string import String
from ee.element import Element
from ee.filter import Filter
from ee.geometry import Geometry
from ee.image import Image
from ee.imagecollection import ImageCollection
from ee.join import Join
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import CompositeMethod, DType, ResamplingMethod
from ...utils.rasterio import WGS84
from ...utils.spectral_indices.spectral_index import SpectralIndex
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
    spectral_indices: list[SpectralIndex] | None = None
    add_cloud_mask: bool = False

    @property
    def bands(self) -> list[str]:
        return self._bands

    @property
    def default_selected_bands(self) -> list[str]:
        return self._default_selected_bands

    @property
    def pixel_range(self):
        return {
            "B1": (0, 900),  # Coastal aerosol
            "B2": (0, 1800),  # Blue
            "B3": (0, 1800),  # Green
            "B4": (0, 1800),  # Red
            "B5": (0, 1800),  # Red Edge 1
            "B6": (0, 3600),  # Red Edge 2
            "B7": (0, 3600),  # Red Edge 3
            "B8": (0, 5400),  # NIR
            "B8A": (0, 5400),  # Narrow NIR
            "B9": (0, 5400),  # Water vapor
            "B11": (0, 3600),  # SWIR 1
            "B12": (0, 3600),  # SWIR 2
            "QA60": (0, 1),  # Cloud mask (binary)
            "AOT": (0, 3000),  # Aerosol Optical Thickness
            "WVP": (0, 20000),  # Water Vapor Pressure (scaled)
            "SCL": (0, 11),  # Scene Classification (discrete classes)
            "TCI_R": (0, 255),  # True Color Red (RGB composite)
            "TCI_G": (0, 255),  # True Color Green (RGB composite)
            "TCI_B": (0, 255),  # True Color Blue (RGB composite)
            "MSK_CLDPRB": (0, 100),  # Cloud Probability (percentage)
        }

    @property
    def resolution(self):
        return 10

    @property
    def is_raster(self) -> bool:
        return True

    @property
    def is_preprocessed(self) -> bool:
        return (self.spectral_indices is not None) or (self.add_cloud_mask)

    @staticmethod
    def contains_aoi(bounds: Geometry, im: Image) -> Element:
        contains = im.geometry().contains(bounds, 1)
        return im.set("contains_bounds", contains)

    @classmethod
    def get_monthly_n_least_cloudy_col(
        cls, bounds: Geometry, start_date: str, end_date: str, n: int
    ) -> ImageCollection:
        s2_col = (
            ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(bounds)
            .filterDate(start_date, end_date)
            .map(lambda im: cls.contains_aoi(bounds, im))
            .filter(Filter.eq("contains_bounds", True))
        )

        months = List.sequence(1, 12)

        def add_tile_id(img):
            # extract the tile code from system:index (last 6 chars: _T31UGV)
            tile_id = String(img.get("system:index")).slice(-6)
            return img.set("tile_id", tile_id)

        def by_month(m):
            monthly_imgs = s2_col.filter(Filter.calendarRange(m, m, "month")).map(add_tile_id)
            # sort by cloudiness and take top-n
            return monthly_imgs.sort("CLOUDY_PIXEL_PERCENTAGE").toList(n)

        s2_n_least_cloudy: ImageCollection = ImageCollection.fromImages(
            months.map(by_month).flatten()
        )
        return s2_n_least_cloudy

    @classmethod
    def get_cloudless_col(
        cls,
        bounds: Geometry,
        start_date: str,
        end_date: str,
        cloudless_portion: int,
        cloud_prb_thresh: int,
    ) -> ImageCollection:
        s2_col = (
            ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(bounds)
            .filterDate(start_date, end_date)
            .filter(
                f"CLOUDY_PIXEL_PERCENTAGE<={100 - cloudless_portion} && "
                f"HIGH_PROBA_CLOUDS_PERCENTAGE<={(100 - cloudless_portion) // 2}"
            )
        )
        s2_cloud = (
            ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
            .filterBounds(bounds)
            .filterDate(start_date, end_date)
        )

        s2_cloud = s2_cloud
        s2_col = s2_col.filterDate(start_date, end_date)

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

        s2_cloudless: ImageCollection = ImageCollection(
            Join.saveFirst("s2cloudless").apply(
                primary=s2_col,
                secondary=s2_cloud,
                condition=Filter.equals(leftField="system:index", rightField="system:index"),
            )
        ).map(mask_s2_clouds)
        return s2_cloudless

    @staticmethod
    def get_cloud_mask(s2_col: ImageCollection) -> ImageCollection:
        def add_cloud_mask_band(img: Image) -> Image:
            cloud_mask = Image(img.select("cs").lte(0.6).rename("cloud_shadow_mask").uint8())
            return img.addBands(cloud_mask)

        s2_with_cloud_mask: ImageCollection = s2_col.linkCollection(
            ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"), ["cs"]
        ).map(add_cloud_mask_band)

        return s2_with_cloud_mask

    def get_col(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        cloudless_portion: int = 60,
        cloud_prb_thresh: int = 30,
        n_least_cloudy_monthly: int | None = None,
    ) -> ImageCollection:
        """Get Sentinel-2 cloud free collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
            End date in "YYYY-MM-DD" format.
        cloudless_portion : int
            Threshold for the portion of filled pixels that must be cloud/shadow free (%).
            Images that do not fullfill the requirement are filtered out. Defaults to 60.
        cloud_prb_thresh : int
            Threshold for cloud probability above which a pixel is filtered out (%).
            Defaults to 30.
        n_least_cloudy_monthly: int | None
            Number of least cloudy images to keep in image collection per month.
        Returns
        -------
        s2_cloudless : ImageCollection
        """
        if (start_date is None) or (end_date is None):
            msg = "Missing temporal aoi not configured."
            log.error(msg)
            raise ValueError(msg)

        bounds = aoi.buffer(aoi.hypotenuse / 2).transform(WGS84).to_ee_geometry()

        if n_least_cloudy_monthly:
            s2_col = self.get_monthly_n_least_cloudy_col(
                bounds,
                start_date,
                end_date,
                n_least_cloudy_monthly,
            )
        else:
            s2_col = self.get_cloudless_col(
                bounds, start_date, end_date, cloudless_portion, cloud_prb_thresh
            )

        if self.add_cloud_mask:
            s2_col = self.get_cloud_mask(s2_col)
        for spectral_index in self.spectral_indices or []:
            s2_col = spectral_index.add_spectral_index_band_to_image_collection(s2_cloudless)
        return s2_col

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        cloudless_portion: int = 60,
        cloud_prb_thresh: int = 40,
        n_least_cloudy_monthly: int | None = None,
        add_cloud_mask: bool = False,
        resolution: float = 10,
        spectral_indices: list[SpectralIndex] | None = None,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get a downloadable time series of Sentinel-2 images.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
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
        n_least_cloudy_monthly : int | None
            Number of least cloudy images to keep in image collection per month.
        add_cloud_mask: bool
            Wether to add to the image collection a cloud mask created with
            GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED. Defaults to False.
        resolution: float
            The resolution for the image.
        spectral_indices: list[SpectralIndex] | None
            List of SpectralIndex objects that are used to compute and add spectral
            index bands to the downloaded images. Defaults to None.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s2_im: DownloadableGeedimImageCollection
            A Sentinel-2 time series collection of the specified AOI and time range.
        """
        for kwarg in kwargs:
            log.warning(f"Argument {kwarg} is ignored.")
        self.spectral_indices = spectral_indices
        self.add_cloud_mask = add_cloud_mask
        s2_cloudless = self.get_col(
            aoi,
            start_date,
            end_date,
            cloudless_portion=cloudless_portion,
            cloud_prb_thresh=cloud_prb_thresh,
            n_least_cloudy_monthly=n_least_cloudy_monthly,
        )

        images = {}
        info = s2_cloudless.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(f"Found 0 Sentinel-2 image.Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Sentinel-2 image.")
        for feature in info["features"]:  # type: ignore[index]
            sys_index = feature.get("properties").get("system:index")
            if self.is_preprocessed:
                im = s2_cloudless.filter(Filter.eq("system:index", sys_index)).first()
                footprint = PatchedBaseImage.from_id(
                    f"COPERNICUS/S2_SR_HARMONIZED/{sys_index}"
                ).footprint
            else:
                id_ = feature.get("id")
                footprint = PatchedBaseImage.from_id(id_).footprint
                im = Image(id_)
            if footprint is None:
                raise ValueError(
                    "Ran into image with no footprint. Did you forget to `.clip(aoi)` ?"
                )
            if Polygon(footprint["coordinates"][0]).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                # resample
                im = self.resample_reproject_clip(im, aoi, resampling, resolution)
                # apply dtype
                im = self.convert_dtype(im, dtype)
                images[sys_index] = PatchedBaseImage(im)
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        composite_method: CompositeMethod = CompositeMethod.MEDIAN,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        cloudless_portion: int = 60,
        cloud_prb_thresh: int = 40,
        add_cloud_mask: bool = False,
        resolution: float = 10,
        spectral_indices: list[SpectralIndex] | None = None,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get a downloadable mosaic of Sentinel-2 images.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
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
        add_cloud_mask: bool
            Wether to add to the image collection a cloud mask created with
            GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED. Defaults to False.
        resolution: float
            The resolution for the image.
        spectral_indices: list[SpectralIndex] | None
            List of SpectralIndex objects that are used to compute and add spectral
            index bands to the downloaded images. Defaults to None.
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
        self.spectral_indices = spectral_indices
        self.add_cloud_mask = add_cloud_mask
        s2_cloudless = self.get_col(
            aoi,
            start_date,
            end_date,
            cloudless_portion=cloudless_portion,
            cloud_prb_thresh=cloud_prb_thresh,
        )
        # Apply resampling
        s2_cloudless = s2_cloudless.map(
            lambda img: self.resample_reproject_clip(img, aoi, resampling, resolution)
        )
        bounds = aoi.transform(WGS84).to_ee_geometry()
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
                aoi,
                start_date,
                end_date,
                composite_method,
                dtype,
                resampling,
                new_cloudless_portion,
                cloud_prb_thresh,
                self.add_cloud_mask,
                resolution,
            )
        log.debug(f"Sentinel-2 mosaicking with {n_images} images.")
        return DownloadableGeedimImage(s2_im)

    @property
    def name(self) -> str:
        return "s2"

    @property
    def full_name(self) -> str:
        return "Sentinel-2 (Geedim)"
