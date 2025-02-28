import logging
from typing import Any

from ee.image import Image
from ee.terrain import Terrain
from geobbox import GeoBoundingBox

from ...utils.enums import CompositeMethod, DType
from ...utils.rasterio import WGS84
from ..downloadables import DownloadableGeedimImage, DownloadableGeedimImageCollection
from ..downloadables.geedim import PatchedBaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["NASADEM"]


def compute_slope(data: Image) -> Image:
    slope = Terrain.slope(data)
    return data.addBands(Image(slope))


class NASADEM(SatelliteABC):
    _bands = ["elevation", "num", "slope", "swb"]
    _default_selected_bands = ["elevation", "slope"]

    @property
    def bands(self):
        return self._bands

    @property
    def default_selected_bands(self):
        return self._default_selected_bands

    @property
    def pixel_range(self):
        return {"elevation": (-512, 8768), "slope": (0, 90), "num": (0, 255), "swb": (0, 255)}

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
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        raise ValueError("Time series is not relevant for DEM.")

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEAN,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get NASADEM composite image.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            (Unused) Included for compatibility.
        end_date : str
            (Unused) Included for compatibility.
        composite_method: CompositeMethod
            (Unused) NASADEM is a single static dataset.
        dtype : DType
            The data type for the image.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        dem_im: DownloadableGeedimImage
            A NASADEM composite image.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")

        bounds = aoi.transform(WGS84).to_ee_geometry()
        dem_im = self.get_im().clip(bounds)
        dem_im = self.convert_image(dem_im, dtype)
        return DownloadableGeedimImage(PatchedBaseImage(dem_im))

    @property
    def name(self) -> str:
        return "nasadem"

    @property
    def full_name(self) -> str:
        return "NASADEM"
