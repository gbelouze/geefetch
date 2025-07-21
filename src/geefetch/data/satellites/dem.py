import logging
from typing import Any

from ee.image import Image
from ee.terrain import Terrain
from geobbox import GeoBoundingBox

from ...utils.enums import CompositeMethod, DType, ResamplingMethod
from ..downloadables import DownloadableGeedimImage, DownloadableGeedimImageCollection
from ..downloadables.geedim import PatchedBaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["NASADEM"]


def compute_slope(data: Image) -> Image:
    slope = Terrain.slope(data)
    return data.addBands(Image(slope))


class NASADEM(SatelliteABC):
    _bands = ["elevation", "slope", "swb"]
    _default_selected_bands = ["elevation", "slope"]

    @property
    def bands(self):
        return self._bands

    @property
    def default_selected_bands(self):
        return self._default_selected_bands

    @property
    def pixel_range(self):
        return {"elevation": (-512, 8768), "slope": (0, 90), "swb": (0, 255)}

    @property
    def is_raster(self):
        return True

    @property
    def resolution(self):
        return 30

    def get_im(
        self,
    ) -> Image:
        """Get NASADEM collection.

        Returns
        -------
        dem_im : Image
        """
        return compute_slope(Image("NASA/NASADEM_HGT/001"))

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        raise ValueError("Time series is not relevant for DEM.")

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        composite_method: CompositeMethod = CompositeMethod.MEAN,
        dtype: DType = DType.Float32,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        resolution: float = 30,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get a downloadable NASADEM composite image.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            (Unused) Included for compatibility.
        end_date : str | None
            (Unused) Included for compatibility.
        composite_method: CompositeMethod
            (Unused) NASADEM is a single static dataset.
        dtype : DType
            The data type for the image.
        resampling : ResamplingMethod
            The resampling method to use when processing the image.
        resolution : float
            The resolution for the image.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        dem_im: DownloadableGeedimImage
            A NASADEM composite image.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")

        # resample
        dem_im = self.get_im()
        dem_im = self.resample_reproject_clip(dem_im, aoi, resampling, resolution)
        # apply dtype
        dem_im = self.convert_dtype(dem_im, dtype)
        return DownloadableGeedimImage(PatchedBaseImage(dem_im))

    @property
    def name(self) -> str:
        return "nasadem"

    @property
    def full_name(self) -> str:
        return "NASADEM"
