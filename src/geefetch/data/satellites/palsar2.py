import logging
from typing import Any

import ee
from ee.filter import Filter
from ee.image import Image
from ee.imagecollection import ImageCollection
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import CompositeMethod, DType, P2Orbit, ResamplingMethod
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
    _default_selected_bands = [
        "HH",
        "HV",
    ]

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
    def resolution(self):
        return 25

    @property
    def is_raster(self) -> bool:
        return True

    def get_col(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        orbit: P2Orbit,
    ) -> ImageCollection:
        """Get Palsar 2 collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        orbit : P2Orbit
            The orbit used to filter the collection before mosaicking.

        Returns
        -------
        palsar2_col : ImageCollection
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()

        palsar2_col = (
            ImageCollection("JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
            .filter(Filter.eq("PassDirection", orbit.value))
        )

        return palsar2_col  # type: ignore[no-any-return]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        orbit: P2Orbit = P2Orbit.DESCENDING,
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
        dtype : DType
            The data type for the image
        resampling : ResamplingMethod
            The resampling method to use when processing the image.
        orbit : P2Orbit
            The orbit used to filter the collection before mosaicking.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        p2_im: DownloadableGeedimImageCollection
            A Palsar-2 time series collection of the specified AOI and time range.
        """
        p2_col = self.get_col(aoi, start_date, end_date, orbit)

        images = {}
        info = p2_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(f"Found 0 Palsar-2 image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Palsar-2 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            footprint = PatchedBaseImage.from_id(id_).footprint
            assert footprint is not None
            if Polygon(footprint["coordinates"][0]).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = Image(id_)
                im = self.before_composite(im, resampling, apply_rl=False)
                im = self.after_composite(im, dtype)
                images[id_.removeprefix("JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR/")] = PatchedBaseImage(
                    im
                )
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEAN,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        orbit: P2Orbit = P2Orbit.DESCENDING,
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
        composite_method: CompositeMethod
            The method use to do mosaicking.
        dtype : DType
            The data type for the image
        resampling : ResamplingMethod
            The resampling method to use when processing the image.
        orbit : P2Orbit
            The orbit used to filter the collection before mosaicking
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        p2_im: DownloadableGeedimImage
            A Palsar-2 composite image of the specified AOI and time range.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")

        bounds = aoi.transform(WGS84).to_ee_geometry()
        p2_col = self.get_col(aoi, start_date, end_date, orbit)
        info = p2_col.getInfo()
        n_images = len(info["features"])  # type: ignore
        if n_images > 500:
            log.warning(
                f"Palsar-2 mosaicking with a large amount of images (n={n_images}). "
                "Expect slower download time."
            )
        if n_images == 0:
            log.error(f"Found 0 Palsar-2 image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Palsar-2 image.")
        log.debug(f"Palsar-2 mosaicking with {n_images} images.")
        p2_col = p2_col.map(lambda img: self.before_composite(img, resampling, apply_rl=True))
        p2_im = composite_method.transform(p2_col).clip(bounds)
        p2_im = self.after_composite(p2_im, dtype)
        p2_im = PatchedBaseImage(p2_im)
        return DownloadableGeedimImage(p2_im)

    @property
    def name(self) -> str:
        return "palsar2"

    @property
    def full_name(self) -> str:
        return "Palsar-2"

    @staticmethod
    def before_composite(im: Image, resampling: ResamplingMethod, apply_rl: bool = False) -> Image:
        # Convert from DN to power
        im = im.pow(2)
        # Optionally apply a refined lee filter
        if apply_rl:
            im = refined_lee(im)
        # Apply resampling if specified
        if resampling.value is not None:
            im = im.resample(resampling.value)
        return im

    def after_composite(self, im: Image, dtype: DType) -> Image:
        # Convert from power to gamma0:
        im = im.log10().multiply(10).subtract(83)
        # Apply pixel range and dtype
        im = self.convert_dtype(im, dtype)
        return im


def refined_lee(image: Image) -> Image:
    """
    Apply the Refined Lee filter to reduce speckle noise.
    Parameters
    ----------
    image : Image
        The input image to be filtered.
    Returns
    -------
    Image
        The image with the Refined Lee filter applied.
    """

    def apply_filter(band_name: str) -> Image:
        band = image.select(band_name)
        mean = band.reduceNeighborhood(ee.Reducer.mean(), ee.Kernel.square(3))
        variance = band.reduceNeighborhood(ee.Reducer.variance(), ee.Kernel.square(3))
        weight = variance.divide(variance.add(mean.pow(2)))
        return mean.add(weight.multiply(band.subtract(mean))).rename(band_name)  # type: ignore[no-any-return]

    filtered_hh = apply_filter("HH")
    filtered_hv = apply_filter("HV")
    return image.addBands([filtered_hh, filtered_hv], overwrite=True)
