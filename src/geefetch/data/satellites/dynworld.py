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

__all__ = ["DynWorld"]


class DynWorld(SatelliteABC):
    _bands = [
        "water",
        "trees",
        "grass",
        "flooded_vegetation",
        "crops",
        "shrub_and_scrub",
        "built",
        "bare",
        "snow_and_ice",
        "label",
    ]
    _default_selected_bands = [
        "water",
        "trees",
        "grass",
        "flooded_vegetation",
        "crops",
        "shrub_and_scrub",
        "built",
        "bare",
        "snow_and_ice",
    ]

    @property
    def bands(self) -> list[str]:
        return self._bands

    @property
    def default_selected_bands(self) -> list[str]:
        return self._default_selected_bands

    @property
    def pixel_range(self):
        return 0, 1

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
    ) -> ee.ImageCollection:
        """Get Dynamic World cloud free collection.

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
        dynworld_col : ee.ImageCollection
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()

        return (  # type: ignore[no-any-return]
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterDate(start_date, end_date)
            .filterBounds(bounds)
        )

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get Dynamic World collection.

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
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        dynworld_im: DownloadableGeedimImageCollection
            A Dynamic World time series collection of the specified AOI and time range.
        """
        dynworld_col = self.get_col(aoi, start_date, end_date)

        images = {}
        info = dynworld_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(f"Found 0 Dynamic World image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Dynamic World image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            if Polygon(PatchedBaseImage.from_id(id_).footprint["coordinates"][0]).intersects(
                aoi.to_shapely_polygon()
            ):
                # aoi intersects im
                im = ee.Image(id_)
                im = self.convert_image(im, dtype)
                images[id_.removeprefix("GOOGLE/DYNAMICWORLD/V1/")] = PatchedBaseImage(im)
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        composite_method: CompositeMethod = CompositeMethod.MEDIAN,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get Dynamic World cloud free collection.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
        composite_method: CompositeMethod
        dtype : DType
            The data type for the image
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        dynworld_im : DownloadableGeedimImage
            A Dynamic World composite image of the specified AOI and time range,
            with clouds filtered out.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")
        bounds = aoi.transform(WGS84).to_ee_geometry()
        dynworld_col = self.get_col(
            aoi,
            start_date,
            end_date,
        )
        dynworld_im = composite_method.transform(dynworld_col).clip(bounds)
        dynworld_im = self.convert_image(dynworld_im, dtype)
        dynworld_im = PatchedBaseImage(dynworld_im)
        n_images = len(dynworld_col.getInfo()["features"])  # type: ignore[index]
        if n_images > 500:
            log.warning(
                f"Dynamic World mosaicking with a large amount of images (n={n_images}). "
                "Expect slower download time."
            )
        log.debug(f"Dynamic World mosaicking with {n_images} images.")
        return DownloadableGeedimImage(dynworld_im)

    @property
    def name(self) -> str:
        return "dyn_world"

    @property
    def full_name(self) -> str:
        return "Dynamic World (Geedim)"
