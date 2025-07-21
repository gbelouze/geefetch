import logging
from typing import Any

from ee.ee_date import Date
from ee.ee_list import List
from ee.ee_number import Number
from ee.featurecollection import FeatureCollection
from ee.geometry import Geometry
from ee.image import Image
from ee.imagecollection import ImageCollection
from geobbox import GeoBoundingBox
from shapely import Polygon

from ...utils.enums import CompositeMethod, DType, ResamplingMethod
from ...utils.rasterio import WGS84
from ..downloadables import DownloadableGeedimImage, DownloadableGeedimImageCollection
from ..downloadables.geedim import PatchedBaseImage
from .abc import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["Landsat8"]


PI = 3.14159265359
MAX_SATELLITE_ZENITH = 7.5
MAX_DISTANCE = 1000000
UPPER_LEFT = 0
LOWER_LEFT = 1
LOWER_RIGHT = 2
UPPER_RIGHT = 3


def mask_clouds_and_saturation(im: Image) -> Image:
    """Masks out clouds, cloud shadows, and saturated pixels from a Landsat 8 image."""
    qa = im.select("QA_PIXEL")
    fillBitMask = 1 << 0
    dilatedCloudBitMask = 1 << 1
    cirrusBitMask = 1 << 2
    cloudBitMask = 1 << 3
    cloudShadowBitMask = 1 << 4
    # snowBitMask = (1 << 5)
    # waterBitMask = (1 << 7)

    # Delete cloud pixels
    qaMask = (
        qa.bitwiseAnd(fillBitMask)
        .eq(0)
        .And(qa.bitwiseAnd(dilatedCloudBitMask).eq(0))
        .And(qa.bitwiseAnd(cirrusBitMask).eq(0))
        .And(qa.bitwiseAnd(cloudBitMask).eq(0))
        .And(qa.bitwiseAnd(cloudShadowBitMask).eq(0))
        # .And(qa.bitwiseAnd(snowBitMask).eq(0))
        # .And(qa.bitwiseAnd(waterBitMask).eq(0))
    )
    # Delete saturation pixels
    saturationMask = im.select("QA_RADSAT").eq(0)

    # Apply the scaling factors to the appropriate bands
    # opticalBands = im.select('SR_B.').multiply(0.0000275).add(-0.2)
    # thermalBands = im.select('ST_B.*').multiply(0.00341802).add(149.0)

    # Replace the original bands with the scaled ones and apply the masks
    return im.updateMask(qaMask).updateMask(saturationMask)


def apply_brdf_correction(im: Image) -> Image:
    """Applies BRDF correction to a Landsat 8 image to account for angular effects."""
    date = im.date()
    footprint = List(im.geometry().bounds().bounds().coordinates().get(0))
    sunAz, sunZen = compute_sun_angles(date, footprint)

    viewAz = calculate_view_azimuth(footprint)
    viewZen = calculate_view_zenith(footprint)

    kvol, kvol0 = calculate_brdf_volumetric_kernel(sunAz, sunZen, viewAz, viewZen)
    result = apply_brdf_to_bands(im, kvol.multiply(PI), kvol0.multiply(PI))

    return result


def compute_sun_angles(date: Date, footprint: List) -> tuple[Image, Image]:
    """Calculates the sun azimuth and zenith angles for a given date and footprint."""
    jdp = date.getFraction("year")
    seconds_in_hour = 3600
    hourGMT = Number(date.getRelative("second", "day")).divide(seconds_in_hour)

    latRad = Image.pixelLonLat().select("latitude").multiply(PI / 180)
    longDeg = Image.pixelLonLat().select("longitude")

    # Julian day proportion in radians
    jdpr = jdp.multiply(PI).multiply(2)

    a = List([0.000075, 0.001868, 0.032077, 0.014615, 0.040849])
    meanSolarTime = longDeg.divide(15.0).add(Number(hourGMT))
    localSolarDiff1 = (
        value(a, 0)
        .add(value(a, 1).multiply(jdpr.cos()))
        .subtract(value(a, 2).multiply(jdpr.sin()))
        .subtract(value(a, 3).multiply(jdpr.multiply(2).cos()))
        .subtract(value(a, 4).multiply(jdpr.multiply(2).sin()))
    )

    localSolarDiff2 = localSolarDiff1.multiply(12 * 60)

    localSolarDiff = localSolarDiff2.divide(PI)
    trueSolarTime = meanSolarTime.add(localSolarDiff.divide(60)).subtract(12.0)

    # Hour as an angle
    ah = trueSolarTime.multiply(Number(MAX_SATELLITE_ZENITH * 2).multiply(PI / 180))
    b = List([0.006918, 0.399912, 0.070257, 0.006758, 0.000907, 0.002697, 0.001480])
    delta = (
        value(b, 0)
        .subtract(value(b, 1).multiply(jdpr.cos()))
        .add(value(b, 2).multiply(jdpr.sin()))
        .subtract(value(b, 3).multiply(jdpr.multiply(2).cos()))
        .add(value(b, 4).multiply(jdpr.multiply(2).sin()))
        .subtract(value(b, 5).multiply(jdpr.multiply(3).cos()))
        .add(value(b, 6).multiply(jdpr.multiply(3).sin()))
    )

    cosSunZen = (
        latRad.sin()
        .multiply(delta.sin())
        .add(latRad.cos().multiply(ah.cos()).multiply(delta.cos()))
    )
    sunZen = cosSunZen.acos()

    # sun azimuth from south, turning west
    sinSunAzSW = ah.sin().multiply(delta.cos()).divide(sunZen.sin())
    sinSunAzSW = sinSunAzSW.clamp(-1.0, 1.0)

    cosSunAzSW = (
        latRad.cos()
        .multiply(-1)
        .multiply(delta.sin())
        .add(latRad.sin().multiply(delta.cos()).multiply(ah.cos()))
    ).divide(sunZen.sin())
    sunAzSW = sinSunAzSW.asin()

    sunAzSW = where(cosSunAzSW.lte(0), sunAzSW.multiply(-1).add(PI), sunAzSW)
    sunAzSW = where(cosSunAzSW.gt(0).And(sinSunAzSW.lte(0)), sunAzSW.add(PI * 2), sunAzSW)

    sunAz = sunAzSW.add(PI)
    sunAz = where(sunAz.gt(PI * 2), sunAz.subtract(PI * 2), sunAz)

    footprint_polygon = Geometry.Polygon(footprint)
    sunAz = sunAz.clip(footprint_polygon)
    sunAz = sunAz.rename(["sunAz"])
    sunZen = sunZen.clip(footprint_polygon).rename(["sunZen"])

    return (sunAz, sunZen)


def calculate_view_azimuth(footprint: List) -> Image:
    """Calculates the sensor's view azimuth angle based on the image footprint."""

    def x(point: List) -> Number:
        return Number(List(point).get(0))

    def y(point: List) -> Number:
        return Number(List(point).get(1))

    upperCenter = line_from_coords(footprint, UPPER_LEFT, UPPER_RIGHT).centroid().coordinates()
    lowerCenter = line_from_coords(footprint, LOWER_LEFT, LOWER_RIGHT).centroid().coordinates()
    slope = ((y(lowerCenter)).subtract(y(upperCenter))).divide(
        (x(lowerCenter)).subtract(x(upperCenter))
    )
    slopePerp = Number(-1).divide(slope)
    azimuthLeft = Image(PI / 2).subtract((slopePerp).atan())
    return azimuthLeft.rename(["viewAz"])  # type: ignore[no-any-return]


def calculate_view_zenith(footprint: List) -> Image:
    """Calculates the sensor's view zenith angle based on the image footprint."""
    leftLine = line_from_coords(footprint, UPPER_LEFT, LOWER_LEFT)
    rightLine = line_from_coords(footprint, UPPER_RIGHT, LOWER_RIGHT)
    leftDistance = FeatureCollection(leftLine).distance(MAX_DISTANCE)
    rightDistance = FeatureCollection(rightLine).distance(MAX_DISTANCE)
    viewZenith = (
        rightDistance.multiply(Number(MAX_SATELLITE_ZENITH * 2))
        .divide(rightDistance.add(leftDistance))
        .subtract(Number(MAX_SATELLITE_ZENITH))
        .clip(Geometry.Polygon(footprint))
        .rename(["viewZen"])
    )
    return viewZenith.multiply(PI / 180)  # type: ignore[no-any-return]


def apply_brdf_to_bands(image: Image, kvol: Image, kvol0: Image) -> Image:
    """Applies BRDF correction to each band of a Landsat 8 image."""
    blue = correct_band_reflectance(
        image, "SR_B2", kvol, kvol0, f_iso=0.0774, f_geo=0.0079, f_vol=0.0372
    )
    green = correct_band_reflectance(
        image, "SR_B3", kvol, kvol0, f_iso=0.1306, f_geo=0.0178, f_vol=0.0580
    )
    red = correct_band_reflectance(
        image, "SR_B4", kvol, kvol0, f_iso=0.1690, f_geo=0.0227, f_vol=0.0574
    )
    nir = correct_band_reflectance(
        image, "SR_B5", kvol, kvol0, f_iso=0.3093, f_geo=0.0330, f_vol=0.1535
    )
    swir1 = correct_band_reflectance(
        image, "SR_B6", kvol, kvol0, f_iso=0.3430, f_geo=0.0453, f_vol=0.1154
    )
    swir2 = correct_band_reflectance(
        image, "SR_B7", kvol, kvol0, f_iso=0.2658, f_geo=0.0387, f_vol=0.0639
    )
    return image.select([]).addBands([blue, green, red, nir, swir1, swir2])  # type: ignore[no-any-return]


def correct_band_reflectance(
    image: Image,
    band_name: str,
    kvol: Image,
    kvol0: Image,
    f_iso: float,
    f_geo: float,
    f_vol: float,
) -> Image:
    """Corrects the reflectance of a specific band using BRDF correction factors."""
    iso = Image(f_iso)
    geo = Image(f_geo)
    vol = Image(f_vol)
    pred = vol.multiply(kvol).add(geo.multiply(kvol)).add(iso).rename(["pred"])
    pred0 = vol.multiply(kvol0).add(geo.multiply(kvol0)).add(iso).rename(["pred0"])
    cfac = pred0.divide(pred).rename(["cfac"])
    corr = image.select(band_name).multiply(cfac).rename([band_name])
    return corr  # type: ignore[no-any-return]


def calculate_brdf_volumetric_kernel(
    sunAz: Image, sunZen: Image, viewAz: Image, viewZen: Image
) -> tuple[Image, Image]:
    """Calculates the BRDF correction factors (k_vol and k_vol0) for a given set of angles.

    The Ross-Thick kernel k_vol is calculated as

        kᵥₒₗ  = [(π/2−ξ)⋅cos(ξ) + sin(ξ)] / [cos(θₛ)+cos(θᵥ)] − π/4

    The Ross-Thick kernel at nadir view k_vol0 is kernel when θᵥ=0, is calculated as

        kᵥₒₗ₀ = [(π/2−θₛ)⋅cos(θₛ) + sin(θₛ)] / [cos(θₛ) +  1] − π/4

    where

        ξ = cos⁻¹(cos(θₛ)⋅cos(θᵥ) + sin(θₛ)⋅sin(θᵥ)⋅cos(ϕ))
        θₛ the solar zenith angle `sunZen`
        θᵥ the view zenith angle `viewZen`
        ϕ  the relative azimuth angle `suvAz - viewAz`
    """
    relative_azimuth = sunAz.subtract(viewAz).rename(["relAz"])
    pa1 = viewZen.cos().multiply(sunZen.cos())
    pa2 = viewZen.sin().multiply(sunZen.sin()).multiply(relative_azimuth.cos())
    phase_angle1 = pa1.add(pa2)
    phase_angle = phase_angle1.acos()
    p1 = Image(PI / 2).subtract(phase_angle)
    p2 = p1.multiply(phase_angle1)
    p3 = p2.add(phase_angle.sin())
    p4 = sunZen.cos().add(viewZen.cos())
    p5 = Image(PI / 4)

    kvol = p3.divide(p4).subtract(p5).rename(["kvol"])

    viewZen0 = Image(0)
    pa10 = viewZen0.cos().multiply(sunZen.cos())
    pa20 = viewZen0.sin().multiply(sunZen.sin()).multiply(relative_azimuth.cos())
    phase_angle10 = pa10.add(pa20)
    phase_angle0 = phase_angle10.acos()
    p10 = Image(PI / 2).subtract(phase_angle0)
    p20 = p10.multiply(phase_angle10)
    p30 = p20.add(phase_angle0.sin())
    p40 = sunZen.cos().add(viewZen0.cos())
    p50 = Image(PI / 4)

    kvol0 = p30.divide(p40).subtract(p50).rename(["kvol0"])

    return (kvol, kvol0)


def line_from_coords(coordinates: List, fromIndex: int, toIndex: int) -> Geometry:
    return Geometry.LineString(  # type: ignore[no-any-return]
        List([coordinates.get(fromIndex), coordinates.get(toIndex)])
    )


def where(condition: Image, trueValue: Image, falseValue: Image) -> Image:
    trueMasked = trueValue.mask(condition)
    falseMasked = falseValue.mask(invertMask(condition))
    return trueMasked.unmask(falseMasked)


def invertMask(mask: Image) -> Image:
    return mask.multiply(-1).add(1)


def value(list: List, index: int) -> Number:
    return Number(list.get(index))


class Landsat8(SatelliteABC):
    _bands = [
        "SR_B1",
        "SR_B2",
        "SR_B3",
        "SR_B4",
        "SR_B5",
        "SR_B6",
        "SR_B7",
        # "QA_PIXEL"
    ]
    _default_selected_bands = [
        "SR_B2",
        "SR_B3",
        "SR_B4",
        "SR_B5",
    ]

    @property
    def bands(self) -> list[str]:
        return self._bands

    @property
    def default_selected_bands(self) -> list[str]:
        return self._default_selected_bands

    @property
    def pixel_range(self):
        return 0, 65455

    @property
    def resolution(self):
        return 30

    @property
    def is_raster(self) -> bool:
        return True

    def get_col(
        self, aoi: GeoBoundingBox, start_date: str | None = None, end_date: str | None = None
    ) -> ImageCollection:
        """Get Landsat 8 collection.

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
        landsat_col : ImageCollection
        """
        bounds = aoi.buffer(10_000).transform(WGS84).to_ee_geometry()

        landsat_col = ImageCollection("LANDSAT/LC08/C02/T1_L2")
        if start_date is not None and end_date is not None:
            landsat_col = landsat_col.filterDate(start_date, end_date)
        landsat_col = landsat_col.filterBounds(bounds)

        return landsat_col.map(mask_clouds_and_saturation).map(apply_brdf_correction)  # type: ignore[no-any-return]

    def get_time_series(
        self,
        aoi: GeoBoundingBox,
        start_date: str | None = None,
        end_date: str | None = None,
        dtype: DType = DType.UInt16,
        resampling: ResamplingMethod = ResamplingMethod.BILINEAR,
        resolution: float = 30,
        **kwargs: Any,
    ) -> DownloadableGeedimImageCollection:
        """Get a downloadable time series of Landsat 8 images.

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
        resampling : ResamplingMethod
            The resampling method to use when processing the image.
        resolution : float
            The resolution for the image.
        **kwargs : Any
            Accepted but ignored additional arguments.

        Returns
        -------
        landsat_im: DownloadableGeedimImageCollection
            A Landsat 8 time series collection of the specified AOI and time range.
        """
        for kwarg in kwargs:
            log.warning(f"Argument {kwarg} is ignored.")
        landsat_col = self.get_col(aoi, start_date, end_date)

        images = {}
        info = landsat_col.getInfo()
        n_images = len(info["features"])  # type: ignore[index]
        if n_images == 0:
            log.error(f"Found 0 Landsat 8 image." f"Check region {aoi.transform(WGS84)}.")
            raise RuntimeError("Collection of 0 Landsat 8 image.")
        for feature in info["features"]:  # type: ignore[index]
            id_ = feature["id"]
            footprint = PatchedBaseImage.from_id(id_).footprint
            assert footprint is not None
            if Polygon(footprint["coordinates"][0]).intersects(aoi.to_shapely_polygon()):
                # aoi intersects im
                im = Image(id_)
                # resample
                im = self.resample_reproject_clip(im, aoi, resampling, resolution)
                # apply dtype
                im = self.convert_dtype(im, dtype)
                images[id_.removeprefix("LANDSAT/LC08/C02/T1_L2/")] = PatchedBaseImage(im)
        return DownloadableGeedimImageCollection(images)

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
        """Get a downloadable mosaic of Landsat 8 images.

        Parameters
        ----------
        aoi : GeoBoundingBox
            Area of interest.
        start_date : str | None
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
            End date in "YYYY-MM-DD" format.
        composite_method : CompositeMethod
            The method to use for compositing the images.
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
        landsat_im : DownloadableGeedimImage
            A Landsat 8 composite image of the specified AOI and time range.
        """
        for key in kwargs:
            log.warning(f"Argument {key} is ignored.")
        landsat_col = self.get_col(aoi, start_date, end_date)
        # Apply resampling
        landsat_col = landsat_col.map(
            lambda img: self.resample_reproject_clip(img, aoi, resampling, resolution)
        )
        bounds = aoi.transform(WGS84).to_ee_geometry()
        landsat_im = composite_method.transform(landsat_col).clip(bounds)
        # Apply dtype
        landsat_im = self.convert_dtype(landsat_im, dtype)
        landsat_im = PatchedBaseImage(landsat_im)
        n_images = len(landsat_col.getInfo()["features"])  # type: ignore[index]
        if n_images > 500:
            log.warning(
                f"Landsat 8 mosaicking with a large amount of images (n={n_images}). "
                "Expect slower download time."
            )
            log.info("Change cloud masking parameters to lower the amount of images.")
        if n_images == 0:
            log.error(
                f"Found 0 Landsat 8 image for given parameters. Check region {aoi.transform(WGS84)}"
            )
        log.debug(f"Landsat 8 mosaicking with {n_images} images.")
        return DownloadableGeedimImage(landsat_im)

    @property
    def name(self) -> str:
        return "landsat8"

    @property
    def full_name(self) -> str:
        return "Landsat-8"
