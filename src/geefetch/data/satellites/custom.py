import logging
from pathlib import Path
from typing import Any

from ee.ee_exception import EEException
from ee.image import Image
from ee.imagecollection import ImageCollection
from geobbox import GeoBoundingBox

from ...utils.enums import CompositeMethod, DType, ResamplingMethod
from ...utils.rasterio import WGS84
from ..downloadables import DownloadableGeedimImage, DownloadableGeedimImageCollection
from ..downloadables.geedim import PatchedBaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["CustomSatellite"]


class CustomSatellite(SatelliteABC):
    """Satellite class to download from any Google Earth Engine Image Collection.

    Parameters
    ----------
    url : str
        Google Earth Engine image collection id
    pixel_range : tuple[float, float] | dict[str, tuple[float, float]]
        The range of pixels in all bands. Defaults to (0, 1).
    name : str | None
        The name for the custom satellite. If None, one is crafted from `url`. Defaults to None.


    """

    def __init__(
        self,
        url: str,
        pixel_range: tuple[float, float] | dict[str, tuple[float, float]] = (0, 1),
        name: str | None = None,
    ):
        self.url = url
        self._pixel_range = pixel_range
        # ugly hack to get something passable as a file name
        self._name = name if name is not None else Path(self.url).name

    @property
    def bands(self):
        return NotImplementedError

    @property
    def default_selected_bands(self):
        raise NotImplementedError

    @property
    def pixel_range(self):
        return self._pixel_range

    @property
    def resolution(self):
        raise NotImplementedError

    @property
    def is_raster(self) -> bool:
        return True

    def get_im(
        self,
        aoi: GeoBoundingBox,
    ) -> Image:
        """Get collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.

        Returns
        -------
        col : ImageCollection
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()
        im = Image(self.url)
        return (  # type: ignore[no-any-return]
            im.clip(bounds)
        )

    def get_col(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ImageCollection:
        """Get collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
            End date in "YYYY-MM-DD" format.

        Returns
        -------
        col : ImageCollection
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()
        col = ImageCollection(self.url)
        if start_date is not None and end_date is not None:
            col = col.filterDate(start_date, end_date)

        return (  # type: ignore[no-any-return]
            col.filterBounds(bounds)
        )

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        raise ValueError("Time series is not implemented for custom satellite.")

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        composite_method: CompositeMethod = CompositeMethod.MEDIAN,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        resolution: float = 30,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get an image from a custom dataset.

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
        resampling : ResamplingMethod
            The resampling method to use when processing the image.
        resolution : float
            The resolution for the image.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        im : DownloadableGeedimImage
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")
        bounds = aoi.transform(WGS84).to_ee_geometry()
        try:
            col = self.get_col(
                aoi,
                start_date,
                end_date,
            )
            # Apply resampling
            col = col.map(
                lambda img: self.resample_reproject_clip(img, aoi, resampling, resolution)
            )
            n_images = len(col.getInfo()["features"])  # type: ignore[index]
            if n_images > 500:
                log.warning(
                    f"Mosaicking with a large amount of images (n={n_images}). "
                    "Expect slower download time."
                )
            log.debug(f"Mosaicking with {n_images} images.")
            im = composite_method.transform(col).clip(bounds)
        except EEException:
            # kinda ugly but there is no easy way to know whether the URL is
            # an Image or an ImageCollection
            im = self.get_im(aoi)

        im = self.convert_dtype(im, dtype)
        im = PatchedBaseImage(im)
        return DownloadableGeedimImage(im)

    @property
    def name(self) -> str:
        return self._name

    @property
    def full_name(self) -> str:
        return f"CustomSatellite({self.name})"
