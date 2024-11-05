"""Utilites to retrieve an image collection of GEDI images, with bad data points filtered out.
"""

import logging
from enum import Enum
from typing import Any, List, Optional

import ee
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

__all__ = ["GEDIvector", "GEDIraster"]


class EsaClass(Enum):
    TREE_COVER = 10
    SHRUB_COVER = 20
    GRASS_COVER = 30
    CROP_COVER = 40
    BUILD_UP = 50
    WATER_BODY = 80


def inList(band: ee.Image, values: List[int | float]) -> ee.Image:
    if not values:
        raise ValueError("Values must contain at least one element")
    mask = band.eq(values.pop())
    for v in values:
        mask = mask.Or(band.eq(v))
    return mask


def rangeContains(band: ee.Image, mini: int | float, maxi: int | float) -> ee.Image:
    return band.gte(mini).And(band.lte(maxi))


def qualityFilter(strict: bool = False) -> ee.Filter:
    filter = ee.Filter.And(
        ee.Filter.rangeContains("rh98", 0, 80),
        ee.Filter.eq("quality_flag", 1),
        ee.Filter.eq("degrade_flag", 0),
        ee.Filter.inList("beam", [5, 6, 8, 11]),  # Full power beams
        ee.Filter.eq("elevation_bias_flag", 0),
        ee.Filter.gte("sensitivity", 0.98),
    )

    if strict:
        filter = ee.Filter.And(
            filter,
            ee.Filter.Or(
                ee.Filter.rangeContains("solar_azimuth", 70, 120),
                ee.Filter.rangeContains("solar_azimuth", 240, 290),
            ),
            ee.Filter.lte("solar_elevation", -10),
            ee.Filter.gte("energy_total", 5_000),
        )
    return filter  # type: ignore[no-any-return]


def relaxedQualityFilter(strict: bool = False) -> ee.Filter:
    filter = ee.Filter.And(
        ee.Filter.rangeContains("rh98", 0, 80),
        ee.Filter.eq("quality_flag", 1),
        ee.Filter.eq("degrade_flag", 0),
        ee.Filter.inList("beam", [5, 6, 8, 11]),  # Full power beams
        ee.Filter.eq("elevation_bias_flag", 0),
        ee.Filter.Or(
            ee.Filter.And(
                ee.Filter.rangeContains("rh98", 0, 5.0),
                ee.Filter.gte("sensitivity", 0.9),
            ),
            ee.Filter.And(
                ee.Filter.rangeContains("rh98", 5, 80),
                ee.Filter.gte("sensitivity", 0.97),
            ),
        ),
    )
    return filter  # type: ignore[no-any-return]


def qualityMask(
    data: ee.Image, esa: Optional[ee.Image] = None, strict: bool = False
) -> ee.Image:
    rh98 = data.select("rh98")
    data = data.updateMask(
        rangeContains(rh98, 0, 80)
        .And(data.select("quality_flag").eq(1))
        .And(data.select("degrade_flag").eq(0))
        .And(inList(data.select("beam"), [5, 6, 8, 11]))
        .And(data.select("elevation_bias_flag").eq(0))
        .And(data.select("sensitivity").gte(0.98))
    )
    if strict:
        data = data.updateMask(
            data.select("modis_treecover")
            .gte(0.01)
            .And(
                rangeContains(data.select("solar_azimuth"), 70, 120).Or(
                    rangeContains(data.select("solar_azimuth"), 240, 290)
                )
            )
            .And(data.select("solar_elevation").gte(10))
            .And(data.select("energy_total").gte(5_000))
        )
    if esa is not None:
        selected_alg = data.select("selected_algorithm")
        data = data.updateMask(
            (
                esa.eq(EsaClass.TREE_COVER)
                .Or(esa.eq(EsaClass.GRASS_COVER).And(rh98.lt(5)))
                .Or(esa.eq(EsaClass.SHRUB_COVER))
                .Or(esa.eq(EsaClass.BUILD_UP).And(rh98.lt(5)))
                .Or(esa.eq(EsaClass.CROP_COVER).And(rh98.lt(5)))
            ).And(
                selected_alg.eq(2).Or(
                    selected_alg.eq(1).And(
                        esa.eq(EsaClass.TREE_COVER).And(rh98.gte(10))
                    )
                )
            )
        )
    return data


def relaxedQualityMask(
    data: ee.Image, esa: Optional[ee.Image] = None, strict: bool = False
) -> ee.Image:
    rh98 = data.select("rh98")
    data = data.updateMask(rangeContains(rh98, 0, 80))
    return data


class GEDIvector(SatelliteABC):
    @property
    def bands(self):
        raise NotImplementedError

    @property
    def selected_bands(self):
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
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        raise NotImplementedError

    def get(
        self, aoi: GeoBoundingBox, start_date: str, end_date: str, **kwargs: Any
    ) -> DownloadableGEECollection:
        """Get GEDI collection.

        Parameters
        ----------
        aoi : ee.Geometry
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.

        Returns
        -------
        gedi_cols : ee.FeatureCollection
            A collection of GEDI points over the specified AOI and time period.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")
        aoi_wgs84 = aoi.transform(WGS84)
        if aoi_wgs84.top > 51.6:
            log.warn(
                f"No GEDI data is collected above latitude 51.6°N."
                f"Your AOI up to latitude {aoi_wgs84.top:.1f}° will not be fully represented."
            )
        if aoi_wgs84.bottom < -51.6:
            log.warn(
                f"No GEDI data is collected bellow latitude 51.6°S."
                f"Your AOI down to latitude {aoi_wgs84.bottom:.1f}° will not be fully represented."
            )
        table_ids = (
            ee.FeatureCollection("LARSE/GEDI/GEDI02_A_002_INDEX")
            .filterBounds(aoi.to_ee_geometry())
            .filter(f'time_start > "{start_date}" && time_end < "{end_date}"')
        )
        gedi_ids = [
            feature["properties"]["table_id"]
            for feature in table_ids.getInfo()["features"]
        ]
        gedi_filter = relaxedQualityFilter()
        collections = [
            (
                ee.FeatureCollection(gedi_id)
                .filterBounds(aoi.to_ee_geometry())
                .filter(gedi_filter)
            )
            for gedi_id in gedi_ids
        ]
        return DownloadableGEECollection(
            ee.FeatureCollection(ee.List(collections)).flatten()
        )

    @property
    def name(self) -> str:
        return "gedi_vector"

    @property
    def full_name(self) -> str:
        return "Gedi (Vectorized)"

    @property
    def is_raster(self) -> bool:
        return False


class GEDIraster(SatelliteABC):
    @property
    def bands(self):
        raise NotImplementedError

    @property
    def selected_bands(self):
        return ["rh98"]

    @property
    def pixel_range(self):
        return 0, 100

    def convert_image(self, im: ee.Image, dtype: DType) -> ee.Image:
        match dtype:
            case DType.Float32:
                return im
            case DType.UInt16:
                min_p, max_p = self.pixel_range
                return im.add(-min_p).multiply((2**16 - 1) / (max_p - min_p)).toUint16()
            case DType.UInt8:
                min_p, max_p = self.pixel_range
                return im.add(-min_p).multiply((2**8 - 1) / (max_p - min_p)).toUint8()
            case _:
                raise ValueError(f"Unsupported {dtype=}.")

    def get_col(
        self, aoi: GeoBoundingBox, start_date: str, end_date: str
    ) -> ee.ImageCollection:
        """Get GEDI collection.

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
        gedi_col : ee.ImageCollection
            A GEDI collection of the specified AOI and time range.
        """
        return (  # type: ignore[no-any-return]
            ee.ImageCollection("LARSE/GEDI/GEDI02_A_002_MONTHLY")
            .filterBounds(aoi.buffer(10_000).to_ee_geometry())
            .filterDate(start_date, end_date)
            .map(qualityMask)
            .select(self.selected_bands)
        )

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get GEDI collection.

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
            if Polygon(
                PatchedBaseImage.from_id(id_).footprint["coordinates"][0]
            ).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = ee.Image(id_)
                im = self.convert_image(im, dtype)
                images[id_.removeprefix("LARSE/GEDI/GEDI02_A_002_MONTHLY/")] = (
                    PatchedBaseImage(im)
                )
        return DownloadableGeedimImageCollection(images)

    def get(
        self,
        aoi: GeoBoundingBox,
        start_date: str,
        end_date: str,
        dtype: DType = DType.Float32,
        **kwargs: Any,
    ) -> DownloadableGeedimImage:
        """Get GEDI collection.

        Parameters
        ----------
        aoi : ee.Geometry
            Area of interest.
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str
            End date in "YYYY-MM-DD" format.
            Percentage of cloud above which the whole image is filtered out.

        Returns
        -------
        gedi_col : ee.ImageCollection
            The GEDI collection of the specified AOI and time range.
        """
        for key in kwargs.keys():
            log.warn(f"Argument {key} is ignored.")
        aoi_wgs84 = aoi.transform(WGS84)
        if aoi_wgs84.top > 51.6:
            log.warn(
                f"No GEDI data is collected above latitude 51.6°N."
                f"Your AOI up to latitude {aoi_wgs84.top:.1f}° will not be fully represented."
            )
        if aoi_wgs84.bottom < -51.6:
            log.warn(
                f"No GEDI data is collected bellow latitude 51.6°S."
                f"Your AOI down to latitude {aoi_wgs84.bottom:.1f}° will not be fully represented."
            )
        gedi_col = self.get_col(aoi, start_date, end_date)
        gedi_im = gedi_col.mosaic()
        gedi_im = self.convert_image(gedi_im, dtype)
        return DownloadableGeedimImage(PatchedBaseImage(gedi_im))

    @property
    def name(self) -> str:
        return "gedi_raster"

    @property
    def full_name(self) -> str:
        return "Gedi (Rasterized)"

    @property
    def is_raster(self) -> bool:
        return True
