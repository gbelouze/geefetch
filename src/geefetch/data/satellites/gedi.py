"""Utilites to retrieve an image collection of GEDI images, with bad data points filtered out."""

import logging
from enum import Enum
from typing import Any

import ee
from ee.ee_list import List as eeList
from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from ee.image import Image
from ee.imagecollection import ImageCollection
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import DType
from ...utils.rasterio import WGS84
from ..downloadables import (
    DownloadableGEECollection,
    DownloadableGeedimImage,
    DownloadableGeedimImageCollection,
)
from ..downloadables.geedim import PatchedBaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["GEDIL2Avector", "GEDIL2Araster", "GEDIL2Bvector"]


class EsaClass(Enum):
    TREE_COVER = 10
    SHRUB_COVER = 20
    GRASS_COVER = 30
    CROP_COVER = 40
    BUILD_UP = 50
    WATER_BODY = 80


def inList(band: Image, values: list[int | float]) -> Image:
    if not values:
        raise ValueError("Values must contain at least one element")
    mask = band.eq(values.pop())
    for v in values:
        mask = mask.Or(band.eq(v))
    return mask


def rangeContains(band: Image, mini: int | float, maxi: int | float) -> Image:
    return band.gte(mini).And(band.lte(maxi))


def l2AQualityFilter() -> Filter:
    filter = Filter.And(
        Filter.rangeContains("rh98", 0, 80),
        Filter.eq("quality_flag", 1),
        Filter.eq("degrade_flag", 0),
        # Filter.inList("beam", [5, 6, 8, 11]),  # Full power beams
        Filter.lte("solar_elevation", 0),
        Filter.gte("sensitivity", 0.9),
    )
    return filter  # type: ignore[no-any-return]


def l2BQualityFilter() -> Filter:
    filter = Filter.And(
        Filter.eq("l2b_quality_flag", 1),
        Filter.eq("degrade_flag", 0),
        Filter.inList("beam", [5, 6, 8, 11]),  # Full power beams
        Filter.gte("sensitivity", 0.9),
    )
    return filter  # type: ignore[no-any-return]


def l2AQualityMask(data: Image) -> Image:
    data = data.updateMask(
        rangeContains(data.select("rh98"), 0, 80)
        .And(data.select("quality_flag").eq(1))
        .And(data.select("degrade_flag").eq(0))
        # .And(inList(data.select("beam"), [5, 6, 8, 11]))
        .And(data.select("solar_elevation").lte(0))
        .And(data.select("sensitivity").gte(0.9))
    )
    return data


class GEDIL2Avector(SatelliteABC):
    @property
    def bands(self):
        raise NotImplementedError

    @property
    def default_selected_bands(self) -> list[str]:
        return [
            "beam",
            "degrade_flag",
            "delta_time",
            "elevation_bias_flag",
            "energy_total",
            "modis_treecover",
            "orbit_number",
            "quality_flag",
            "rh98",
            "selected_algorithm",
            "sensitivity",
            "solar_azimuth",
            "solar_elevation",
        ]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        raise NotImplementedError

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> DownloadableGEECollection:
        """Get a downloadable collection of GEDI L2A vector points.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
            End date in "YYYY-MM-DD" format.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        gedi_cols : DownloadableGEECollection
            A collection of GEDI points over the specified AOI and time period.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")
        aoi_wgs84 = aoi.transform(WGS84)
        if aoi_wgs84.top > 51.6:
            log.warning(
                f"No GEDI data is collected above latitude 51.6°N."
                f"Your AOI up to latitude {aoi_wgs84.top:.1f}° will not be fully represented."
            )
        if aoi_wgs84.bottom < -51.6:
            log.warning(
                f"No GEDI data is collected bellow latitude 51.6°S."
                f"Your AOI down to latitude {aoi_wgs84.bottom:.1f}° will not be fully represented."
            )
        table_ids = (
            FeatureCollection("LARSE/GEDI/GEDI02_A_002_INDEX")
            .filterBounds(aoi.to_ee_geometry())
            .filter(f'time_start > "{start_date}" && time_end < "{end_date}"')
        )
        gedi_ids = [
            feature["properties"]["table_id"] for feature in table_ids.getInfo()["features"]
        ]
        gedi_filter = l2AQualityFilter()
        collections = [
            (FeatureCollection(gedi_id).filterBounds(aoi.to_ee_geometry()).filter(gedi_filter))
            for gedi_id in gedi_ids
        ]
        return DownloadableGEECollection(FeatureCollection(eeList(collections)).flatten())

    @property
    def name(self) -> str:
        return "gedi_l2a_vector"

    @property
    def full_name(self) -> str:
        return "Gedi (Vectorized)"

    @property
    def is_raster(self) -> bool:
        return False


class GEDIL2Araster(SatelliteABC):
    @property
    def bands(self):
        return ee.ImageCollection("LARSE/GEDI/GEDI02_A_002_MONTHLY").first().bandNames().getInfo()

    @property
    def default_selected_bands(self) -> list[str]:
        return ["rh98"]

    @property
    def pixel_range(self):
        return 0, 100

    def get_col(
        self, aoi: GeoBoundingBox, start_date: str | None = None, end_date: str | None = None
    ) -> ImageCollection:
        """Get GEDI L2A image collection.

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
        gedi_col : ImageCollection
            A GEDI collection of the specified AOI and time range.
        """
        col = ImageCollection("LARSE/GEDI/GEDI02_A_002_MONTHLY").filterBounds(
            aoi.buffer(10_000).to_ee_geometry()
        )
        if start_date is not None and end_date is not None:
            col = col.filterDate(start_date, end_date)
        return (  # type: ignore[no-any-return]
            col.map(l2AQualityMask).select(self.default_selected_bands)
        )

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get GEDI L2A time series collection.

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
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        gedi_im: DownloadableGeedimImageCollection
            A GEDI time series collection of the specified AOI and time range.
        """
        gedi_col = self.get_col(aoi, start_date, end_date)

        images = {}
        info = gedi_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(f"Found 0 GEDI image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 GEDI image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            footprint = PatchedBaseImage.from_id(id_).footprint
            if footprint is None:
                raise RuntimeError(f"Could not retrieve footprint for GEE image with id {id_}.")
            if Polygon(footprint["coordinates"][0]).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = Image(id_)
                # apply dtype
                im = self.convert_dtype(im, dtype)
                images[id_.removeprefix("LARSE/GEDI/GEDI02_A_002_MONTHLY/")] = PatchedBaseImage(im)
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get GEDI L2A Image.

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
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        gedi_col : DownloadableGeedimImage
            The GEDI collection of the specified AOI and time range.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")
        aoi_wgs84 = aoi.transform(WGS84)
        if aoi_wgs84.top > 51.6:
            log.warning(
                f"No GEDI data is collected above latitude 51.6°N."
                f"Your AOI up to latitude {aoi_wgs84.top:.1f}° will not be fully represented."
            )
        if aoi_wgs84.bottom < -51.6:
            log.warning(
                f"No GEDI data is collected bellow latitude 51.6°S."
                f"Your AOI down to latitude {aoi_wgs84.bottom:.1f}° will not be fully represented."
            )
        gedi_col = self.get_col(aoi, start_date, end_date)
        bounds = aoi.transform(WGS84).to_ee_geometry()
        gedi_im = gedi_col.mosaic().clip(bounds)
        gedi_im = self.convert_dtype(gedi_im, dtype)
        return DownloadableGeedimImage(PatchedBaseImage(gedi_im))

    @property
    def name(self) -> str:
        return "gedi_l2a_raster"

    @property
    def full_name(self) -> str:
        return "Gedi (Rasterized)"

    @property
    def is_raster(self) -> bool:
        return True


class GEDIL2Bvector(SatelliteABC):
    @property
    def bands(self):
        raise NotImplementedError

    @property
    def default_selected_bands(self) -> list[str]:
        return [
            "pai",
            "beam",
            "degrade_flag",
            "delta_time",
            "shot_number",
            "l2b_quality_flag",
            "selected_l2a_algorithm",
            "sensitivity",
            "solar_azimuth",
            "solar_elevation",
        ]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        raise NotImplementedError

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> DownloadableGEECollection:
        """Get a downloadable collection of GEDI L2B vector points.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
            End date in "YYYY-MM-DD" format.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        gedi_l2b_cols : DownloadableGEECollection
            A collection of GEDI L2B points over the specified AOI and time period.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")
        aoi_wgs84 = aoi.transform(WGS84)
        if aoi_wgs84.top > 51.6:
            log.warning(
                f"No GEDI data is collected above latitude 51.6°N."
                f"Your AOI up to latitude {aoi_wgs84.top:.1f}° will not be fully represented."
            )
        if aoi_wgs84.bottom < -51.6:
            log.warning(
                f"No GEDI data is collected bellow latitude 51.6°S."
                f"Your AOI down to latitude {aoi_wgs84.bottom:.1f}° will not be fully represented."
            )
        table_ids = (
            FeatureCollection("LARSE/GEDI/GEDI02_B_002_INDEX")
            .filterBounds(aoi.to_ee_geometry())
            .filter(f'time_start > "{start_date}" && time_end < "{end_date}"')
        )
        gedi_l2b_ids = [
            feature["properties"]["table_id"] for feature in table_ids.getInfo()["features"]
        ]
        gedi_l2b_filter = l2BQualityFilter()
        collections = [
            (
                FeatureCollection(gedi_l2b_id)
                .filterBounds(aoi.to_ee_geometry())
                .filter(gedi_l2b_filter)
            )
            for gedi_l2b_id in gedi_l2b_ids
        ]
        return DownloadableGEECollection(FeatureCollection(eeList(collections)).flatten())

    @property
    def name(self) -> str:
        return "gedi_l2b_vector"

    @property
    def full_name(self) -> str:
        return "GEDI L2B (Vectorized)"

    @property
    def is_raster(self) -> bool:
        return False
