import logging
from typing import Any

import ee
from ee.filter import Filter
from ee.image import Image
from ee.imagecollection import ImageCollection
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import CompositeMethod, DType, ResamplingMethod, S1Orbit
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
        selected_bands: list[str] | None = None,
    ) -> ImageCollection:
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
        selected_bands : list[str] | None
            The bands to be downloaded.

        Returns
        -------
        s1_col : ImageCollection
            A Sentinel-1 collection of the specified AOI and time range.
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()
        selected_bands = self.default_selected_bands if selected_bands is None else selected_bands
        self.check_selected_bands(selected_bands)

        # Only accepted combination are [VV], [HH], [HH, HV] or [VV, VH]
        if (
            "VV" in selected_bands
            and ("HH" in selected_bands or "HV" in selected_bands)
            or "HH" in selected_bands
            and "VH" in selected_bands
            or "VH" in selected_bands
            and "VV" not in selected_bands
            or "HV" in selected_bands
            and "HH" not in selected_bands
        ):
            raise ValueError(
                "Only polarization band combination accepted for Sentinel-1 are "
                "[VV], [HH], [HH, HV] or [VV, VH]"
            )

        band_filter = Filter.And(
            *[
                Filter.listContains("transmitterReceiverPolarisation", band)
                for band in selected_bands
                if band != "angle"
            ]
        )
        col = (
            ImageCollection("COPERNICUS/S1_GRD")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
            .filter(band_filter)
            .filter(Filter.eq("instrumentMode", "IW"))
        )

        match orbit:
            case S1Orbit.ASCENDING | S1Orbit.DESCENDING:
                col = col.filter(Filter.eq("orbitProperties_pass", orbit.value))
            case S1Orbit.BOTH:
                pass
            case S1Orbit.AS_BANDS:
                raise ValueError(f"Cannot get S1 collection with {orbit=}")

        return col  # type: ignore[no-any-return]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        orbit: S1Orbit = S1Orbit.ASCENDING,
        selected_bands: list[str] | None = None,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
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
        selected_bands : list[str] | None
            The bands to be downloaded.
        resampling : ResamplingMethod
            The resampling method to use when compositing images.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s1_im: DownloadableGeedimImageCollection
            A Sentinel-1 time series collection of the specified AOI and time range.
        """
        if orbit == S1Orbit.AS_BANDS:
            raise ValueError("Orbit AS_BANDS is not permitted for downloading time series.")
        s1_col = self.get_col(aoi, start_date, end_date, orbit, selected_bands)

        images = {}
        info = s1_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(f"Found 0 Sentinel-1 image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Sentinel-1 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            footprint = PatchedBaseImage.from_id(id_).footprint
            assert footprint is not None
            if Polygon(footprint["coordinates"][0]).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = Image(id_)
                # convert to power and resample
                im = self.before_composite(im, resampling)
                # Apply pixel range and dtype
                im = self.after_composite(im, dtype)
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
        selected_bands: list[str] | None = None,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
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
        selected_bands : list[str] | None
            The bands to be downloaded.
        resampling : ResamplingMethod
            The resampling method to use when compositing images.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s1_im: DownloadableGeedimImage
            A Sentinel-1 composite image of the specified AOI and time range.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")

        def get_im(orbit: S1Orbit) -> Image:
            s1_col = self.get_col(aoi, start_date, end_date, orbit, selected_bands)

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

            # Process all images in the collection
            s1_col = s1_col.map(lambda im: self.before_composite(im, resampling))
            # Create composite
            s1_im = composite_method.transform(s1_col).clip(bounds)
            # Process composite
            s1_im = self.after_composite(s1_im, dtype)
            return s1_im

        match orbit:
            case S1Orbit.ASCENDING | S1Orbit.DESCENDING | S1Orbit.BOTH:
                s1_im = get_im(orbit)
            case S1Orbit.AS_BANDS:
                s1_im_asc = get_im(S1Orbit.ASCENDING).select(selected_bands)
                s1_im_asc = s1_im_asc.rename([f"{band}_ascending" for band in selected_bands])  # type: ignore[union-attr]

                s1_im_desc = get_im(S1Orbit.DESCENDING).select(selected_bands)
                s1_im_desc = s1_im_desc.rename([f"{band}_descending" for band in selected_bands])  # type: ignore[union-attr]

                s1_im = s1_im_asc.addBands(s1_im_desc)

        s1_im = PatchedBaseImage(s1_im)
        return DownloadableGeedimImage(s1_im)

    @staticmethod
    def before_composite(im: Image, resampling: ResamplingMethod) -> Image:
        # Convert from db to power: 10^(im/10)
        im = ee.Image(10).pow(im.divide(10))
        # Apply resampling if specified
        if resampling.value is not None:
            im = im.resample(resampling.value)
        return im

    def after_composite(self, im: Image, dtype: DType) -> Image:
        # Convert from power to db
        im = im.log10().multiply(10)
        # Apply pixel range and dtype
        im = self.convert_dtype(im, dtype)
        return im

    @property
    def name(self) -> str:
        return "s1"

    @property
    def full_name(self) -> str:
        return "Sentinel-1"
