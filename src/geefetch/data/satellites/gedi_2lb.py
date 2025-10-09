"""Utilites to retrieve an image collection of GEDI images, with bad data points filtered out."""

import logging
from typing import Any

from ee.ee_list import List as eeList
from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from ee.image import Image
from geobbox import GeoBoundingBox

from ...utils.enums import DType
from ...utils.rasterio import WGS84
from ..downloadables import DownloadableGEECollection, DownloadableGeedimImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["GEDIL2Bvector"]


def inList(band: Image, values: list[int | float]) -> Image:
    if not values:
        raise ValueError("Values must contain at least one element")
    mask = band.eq(values.pop())
    for v in values:
        mask = mask.Or(band.eq(v))
    return mask


def relaxedQualityFilter() -> Filter:
    filter = Filter.And(
        Filter.eq("l2b_quality_flag", 1),
        Filter.eq("degrade_flag", 0),
        Filter.inList("beam", [5, 6, 8, 11]),  # Full power beams
        Filter.gte("sensitivity", 0.9),
    )
    return filter  # type: ignore[no-any-return]


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
        """Get a downloadable collection of GEDI L2B points.

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
        gedi_l2b_filter = relaxedQualityFilter()
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
