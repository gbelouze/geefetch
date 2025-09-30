import logging
from dataclasses import astuple
from typing import Any

from ee.filter import Filter
from ee.image import Image
from ee.imagecollection import ImageCollection
from gee_s1_processing.border_noise_correction import f_mask_edges
from gee_s1_processing.wrapper import speckle_filter_wrapper, terrain_normalization_wrapper
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...cli.omegaconfig import SpeckleFilterConfig, TerrainNormalizationConfig
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
    speckle_filter_config: SpeckleFilterConfig | None
    terrain_normalization_config: TerrainNormalizationConfig | None

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

    @property
    def is_preprocessed(self):
        return (self.speckle_filter_config is not None) or (
            self.terrain_normalization_config is not None
        )

    def get_col(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        orbit: S1Orbit = S1Orbit.ASCENDING,
        selected_bands: list[str] | None = None,
    ) -> ImageCollection:
        """Get Sentinel-1 collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
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

        # Only accepted combination are [VV], [HH], [VH], [HH, HV] or [VV, VH]
        # Check for invalid combinations
        if (
            ("VV" in selected_bands and "HH" in selected_bands)
            or ("VV" in selected_bands and "HV" in selected_bands)
            or ("HH" in selected_bands and "VH" in selected_bands)
            or ("VH" in selected_bands and "HV" in selected_bands)
        ):
            raise ValueError(
                "Only polarization band combination accepted for Sentinel-1 are "
                "[VV], [HH], [VH], [HV], [HH, HV] or [VV, VH]"
            )

        band_filter = Filter.And(
            *[
                Filter.listContains("transmitterReceiverPolarisation", band)
                for band in selected_bands
                if band != "angle"
            ]
        )
        col = ImageCollection("COPERNICUS/S1_GRD_FLOAT")
        if start_date is not None and end_date is not None:
            col = col.filterDate(start_date, end_date)
        col = col.filterBounds(bounds).filter(band_filter).filter(Filter.eq("instrumentMode", "IW"))

        match orbit:
            case S1Orbit.ASCENDING | S1Orbit.DESCENDING:
                col = col.filter(Filter.eq("orbitProperties_pass", orbit.value))
            case S1Orbit.BOTH:
                pass
            case S1Orbit.AS_BANDS:
                raise ValueError(f"Cannot get S1 collection with {orbit=}")
        col = col.map(f_mask_edges)
        if self.speckle_filter_config:
            col = speckle_filter_wrapper(col, *astuple(self.speckle_filter_config))
        if self.terrain_normalization_config:
            col = terrain_normalization_wrapper(col, *astuple(self.terrain_normalization_config))
        return col  # type: ignore[no-any-return]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        orbit: S1Orbit = S1Orbit.ASCENDING,
        selected_bands: list[str] | None = None,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        resolution: float = 10,
        speckle_filter_config: SpeckleFilterConfig | None = None,
        terrain_normalization_config: TerrainNormalizationConfig | None = None,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get a downloadable time series of Sentinel-1 images.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
            End date in "YYYY-MM-DD" format.
        dtype : DType
            The data type for the image
        orbit : S1Orbit
            The orbit used to filter the collection before mosaicking
        selected_bands : list[str] | None
            The bands to be downloaded.
        resampling : ResamplingMethod
            The resampling method to use when compositing images.
        resolution: float
            The resolution for the image.
        speckle_filter_config : SpeckleFilterConfig | None
        terrain_normalization_config : TerrainNormalizationConfig | None
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s1_im: DownloadableGeedimImageCollection
            A Sentinel-1 time series collection of the specified AOI and time range.
        """
        for key in kwargs:
            if key not in ("speckle_filter_config", "terrain_normalization_config"):
                log.warning(f"Argument {key} is ignored.")

        self.speckle_filter_config = speckle_filter_config
        self.terrain_normalization_config = terrain_normalization_config
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
            sys_index = feature.get("properties").get("system:index")
            if self.is_preprocessed:
                im = s1_col.filter(Filter.eq("system:index", sys_index)).first()
                footprint = PatchedBaseImage.from_id(
                    f"COPERNICUS/S1_GRD_FLOAT/{sys_index}"
                ).footprint
            else:
                id_ = feature.get("id")
                footprint = PatchedBaseImage.from_id(id_).footprint
                im = Image(id_)
            assert footprint is not None
            if Polygon(footprint["coordinates"][0]).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                # convert to power and resample
                im = self.before_composite(im, resampling, aoi, resolution)
                # Apply pixel range and dtype
                im = self.after_composite(im, dtype)
                images[sys_index] = PatchedBaseImage(im)
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        composite_method: CompositeMethod = CompositeMethod.MEAN,
        dtype: DType = DType.Float32,
        orbit: S1Orbit = S1Orbit.ASCENDING,
        selected_bands: list[str] | None = None,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        resolution: float = 10,
        speckle_filter_config: SpeckleFilterConfig | None = None,
        terrain_normalization_config: TerrainNormalizationConfig | None = None,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get a downloadable mosaic of Sentinel-1 images.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
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
        resolution: float
            The resolution for the image.
        speckle_filter_config : SpeckleFilterConfig | None
        terrain_normalization_config : TerrainNormalizationConfig | None
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        s1_im: DownloadableGeedimImage
            A Sentinel-1 composite image of the specified AOI and time range.
        """
        for key in kwargs:
            if key not in ("speckle_filter_config", "terrain_normalization_config"):
                log.warning(f"Argument {key} is ignored.")

        self.speckle_filter_config = speckle_filter_config
        self.terrain_normalization_config = terrain_normalization_config

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

            # Process all images in the collection
            s1_col = s1_col.map(lambda im: self.before_composite(im, resampling, aoi, resolution))
            # Create composite
            bounds = aoi.transform(WGS84).to_ee_geometry()
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

    def before_composite(
        self,
        im: Image,
        resampling: ResamplingMethod,
        aoi: GeoBoundingBox,
        scale: float,
    ) -> Image:
        # Apply resampling if specified
        im = self.resample_reproject_clip(im, aoi, resampling, scale)
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
