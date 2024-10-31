"""Utilities for working with different system of coordinates."""

import logging
import string
import sys
from dataclasses import dataclass
from pathlib import Path

import ee
import numpy as np
import rasterio as rio
import rasterio.warp as warp
import shapely
import utm
from rasterio.crs import CRS

log = logging.getLogger(__name__)

if (sys.version_info.major, sys.version_info.minor) < (3, 10):
    from typing_extensions import Iterator, Optional, Self, TypeAlias
else:
    from typing import Iterator, Optional, Self, TypeAlias

__all__ = ["UTM", "WGS84", "BoundingBox"]


Coordinate: TypeAlias = tuple[float, float]


_UTM_ZONE_LETTERS = tuple(
    char
    for char in string.ascii_uppercase
    if char not in ["A", "B", "I", "O", "Y", "Z"]
)


_EPSILON = 1e-10

WGS84 = CRS.from_epsg(4326)


@dataclass(frozen=True, eq=True)
class UTM:
    zone: int
    letter: str

    def __post_init__(self):
        if self.letter not in _UTM_ZONE_LETTERS:
            raise ValueError(f"Invalid UTM zone letter {self.letter}.")
        if not (1 <= self.zone <= 60):
            raise ValueError(
                f"Invalid UTM zone number {self.zone}. Expected a value in the range [1, 60]."
            )
        # Frozen dataclass hack
        # :see_also: https://stackoverflow.com/questions/53756788/
        #   how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true
        object.__setattr__(self, "_crs", None)

    def __str__(self) -> str:
        return str(self.zone) + self.letter

    @property
    def crs(self) -> CRS:
        """The CRS associated to the UTM zone."""
        if self._crs is not None:  # type: ignore
            return self._crs  # type: ignore
        crs = CRS.from_epsg((32600 if self.hemisphere == "N" else 32700) + self.zone)
        object.__setattr__(self, "_crs", crs)
        return self._crs  # type: ignore

    @property
    def hemisphere(self) -> str:
        """The hemisphere of the UTM region.

        Returns
        -------
        str
            "N" for northern hemisphere and "S" for southern.
        """
        return "N" if self.letter >= "N" else "S"

    def left(self) -> Self:
        """Computes the UTM region left of the current region."""
        return self.__class__((self.zone - 2) % 60 + 1, self.letter)

    def right(self) -> Self:
        """Computes the UTM region right of the current region."""
        return self.__class__(self.zone % 60 + 1, self.letter)

    @classmethod
    def from_latlon(cls, lat: float, lon: float) -> Self:
        """Computes the UTM zone encapsulating the point at the given coordinate.

        Parameters
        ----------
        lat : float
            Point latitude, between 80°S and 84°N (i.e. -80 <= lat <= 84).
        lon : float
            Point longitude, between 180°W and 180°E (i.e. -180 <= lon <= 180).

        Returns
        -------
        Self
        """
        _, _, zone, letter = utm.from_latlon(lat, lon)
        return cls(zone, letter)

    @classmethod
    def utm_hemisphere_from_crs(cls, crs: CRS) -> str:
        """Computes the UTM hemisphere defined by the given `crs`.

        Parameters
        ----------
        crs : CRS
            The Coordinate Reference System, expected to be EPSG:326** or EPSG:327**.

        Returns
        -------
        str
            The hemisphere of the given UTM CRS.
        """
        epsg = crs.to_epsg()
        if 32600 < epsg <= 32660:
            return "N"
        if 32700 < epsg <= 32760:
            return "S"
        raise ValueError(f"{crs} is not a UTM local CRS.")

    @classmethod
    def utm_zone_from_crs(cls, crs: CRS) -> int:
        """Computes the UTM zone defined by the given `crs`.

        Parameters
        ----------
        crs : CRS
            The Coordinate Reference System, expected to be EPSG:326** or EPSG:327**.

        Returns
        -------
        int
            The zone number of the given CRS.
        """
        epsg: int = crs.to_epsg()
        if not (32600 < epsg <= 32660 or 32700 < epsg <= 32760):
            raise ValueError(f"{crs} is not a UTM local CRS.")
        return epsg % 100

    @classmethod
    def is_utm_crs(cls, crs: CRS) -> bool:
        """Whether the given `crs` is a UTM local CRS."""
        epsg: int = crs.to_epsg()
        return 32600 < epsg <= 32660 or 32700 < epsg <= 32760

    @classmethod
    def utm_strip_name_from_crs(cls, crs: CRS) -> str:
        return f"UTM{cls.utm_zone_from_crs(crs)}{cls.utm_hemisphere_from_crs(crs)}"


@dataclass(frozen=True)
class BoundingBox:
    left: float
    bottom: float
    right: float
    top: float
    crs: CRS = WGS84

    def __post_init__(self):
        if self.left > self.right:
            raise ValueError(
                f"BoundingBox is initialized with {self.left=} > {self.right=}"
            )
        if self.bottom > self.top:
            raise ValueError(
                f"BoundingBox is initialized with {self.bottom=} > {self.top=}"
            )

    def __contains__(self, point: Coordinate) -> bool:
        """Whether a point is contained in the bounding box.
        Expects a point in northing/easting coordinate, in a CRS consistent with the bounding box.
        """
        northing, easting = point
        return (
            self.left <= easting <= self.right and self.bottom <= northing <= self.left
        )

    def __and__(self, other: Self) -> Self:
        """Intersection of bounding boxes. Emits a warning if the bboxes are not in the same CRS.

        Returns
        -------
        bbox: BoundingBox
            The intersection of the bboxes expressed in the first one's CRS.
        """
        if other.crs != self.crs:
            log.warn("Intersection between bounding box in different CRS.")
            other = other.transform(self.crs)
        if (
            self.right < other.left
            or other.right < self.left
            or self.top < other.bottom
            or other.top < self.bottom
        ):
            return self.__class__(0, 0, 0, 0, self.crs)
        return self.__class__(
            left=max(self.left, other.left),
            right=min(self.right, other.right),
            top=min(self.top, other.top),
            bottom=max(self.bottom, other.bottom),
            crs=self.crs,
        )

    @property
    def ul(self) -> Coordinate:
        """Compute the coordinate of the upper-left corner of a bounding box, in northing/easting format."""
        return (self.top, self.left)

    @property
    def ur(self) -> Coordinate:
        """Compute the coordinate of the upper-right corner of a bounding box, in northing/easting format."""
        return (self.top, self.right)

    @property
    def ll(self) -> Coordinate:
        """Compute the coordinate of the lower-left corner of a bounding box, in northing/easting format."""
        return (self.bottom, self.left)

    @property
    def lr(self) -> Coordinate:
        """Compute the coordinate of the lower-right corner of a bounding box, in northing/easting format."""
        return (self.bottom, self.right)

    @property
    def center(self) -> Coordinate:
        """Compute the center coordinate of a bounding box, in northing/easting format.

        Returns
        -------
        center: Coordinate
            The center of the bbox expressed in the same CRS.
        """
        return ((self.top + self.bottom) / 2, (self.left + self.right) / 2)

    @property
    def area(self) -> float:
        """Simple estimation of the area of the bounding box, expressed in the units of its CRS."""
        if self.is_empty:
            return 0
        return (self.top - self.bottom) * (self.right - self.left)

    @property
    def is_empty(self) -> bool:
        """Check if a bounding box has an empty interior."""
        return bool(
            (self.right - self.left) < _EPSILON or (self.top - self.bottom) < _EPSILON
        )

    @property
    def is_not_empty(self) -> bool:
        """Check if a bounding box has a non empty interior."""
        return bool(
            (self.right - self.left) > _EPSILON and (self.top - self.bottom) > _EPSILON
        )

    def with_(
        self,
        left: Optional[float] = None,
        bottom: Optional[float] = None,
        right: Optional[float] = None,
        top: Optional[float] = None,
    ) -> Self:
        """Returns a modification of the bounding box with specified changes."""
        return self.__class__(
            left=left if left is not None else self.left,
            bottom=bottom if bottom is not None else self.bottom,
            right=right if right is not None else self.right,
            top=top if top is not None else self.top,
            crs=self.crs,
        )

    def iou(self, other: Self) -> float:
        """Computes the IoU (Intersection over Union) of two bounding boxes.

        Parameters
        ----------
        other : BoundingBox
            An other bounding box, in the same CRS.

        Returns
        -------
        float
            The IoU, a value between 0 and 1.
        """
        inter = self & other
        i = inter.area
        u = self.area + other.area - inter.area
        return i / u

    def intersects(self, other: Self) -> bool:
        """Check if a bounding box has non-empty intersection with another.

        Parameters
        ----------
        other : BoundingBox
            An other bounding box, in the same CRS.

        Returns
        -------
        bool
            True if the two bounding boxes have non empty intersection.
        """
        if other.crs != self.crs:
            log.warn(
                f"Intersection between bounding box in different CRS ({self.crs=}, {other.crs=})."
            )
            other = other.transform(self.crs)
        if self.is_empty:
            return False
        return (
            self.right > other.left
            and other.right > self.left
            and self.top > other.bottom
            and other.top > self.bottom
        )

    def is_contained(self, other: Self) -> bool:
        """Check if a bounding box is fully contained in another.

        Parameters
        ----------
        other : BoundingeBox
            An other bounding box, in the same CRS.

        Returns
        -------
        bool
            True if the first bounding box is fully contained in the other.
        """
        if self.crs != other.crs:
            log.warn(
                f"Containment test between bounding box in different CRS ({self.crs=}, {other.crs=})."
            )
            other = other.transform(self.crs)
        return (
            other.left < self.left < self.right < other.right
            and other.bottom < self.bottom < self.top < other.top
        )

    def buffer(self, buff: float) -> Self:
        """Returns a bounding box increased by a given buffer in all directions.

        Parameters
        ----------
        buff : float

        Returns
        -------
        BoundingBox
            The buffered bounding box.
        """
        if buff < 0:
            raise ValueError(f"Invalid buffer value {buff}. Expected a positive value.")
        return self.with_(
            left=self.left - buff,
            right=self.right + buff,
            bottom=self.bottom - buff,
            top=self.top + buff,
        )

    def unbuffer(self, buff: float) -> Self:
        """Returns a bounding box decreased by a given buffer in all directions, that is, the same bounding box with
        its outer perimeter of given width removed.

        Parameters
        ----------
        buff : float

        Returns
        -------
        BoundingBox
            The unbuffered bounding box.

        ..available:: 0.2.2
        """
        if buff < 0:
            raise ValueError(f"Invalid buffer value {buff}. Expected a positive value.")
        if 2 * buff >= self.right - self.left:
            raise ValueError(
                f"Invalid buffer value {buff} is greater than the half-width of the bbox."
            )
        if 2 * buff >= self.top - self.bottom:
            raise ValueError(
                f"Invalid buffer value {buff} is greater than the half-height of the bbox."
            )
        return self.with_(
            left=self.left + buff,
            right=self.right - buff,
            bottom=self.bottom + buff,
            top=self.top - buff,
        )

    def to_ee_geometry(self) -> ee.Geometry:
        """Translate a bounding box as a ee.Geometry polygon.

        Returns
        -------
        ee.Geometry
            The polygon representing the bbox in Google Earth Engine, in the same CRS.
        """
        geom = ee.Geometry.Polygon(
            [
                [
                    [self.left, self.top],
                    [self.left, self.bottom],
                    [self.right, self.bottom],
                    [self.right, self.top],
                    [self.left, self.top],
                ]
            ],
            proj=f"EPSG:{self.crs.to_epsg()}",
            evenOdd=False,
        )
        return ee.Feature(geom, {}).geometry()  # type: ignore[no-any-return]

    def to_shapely_polygon(self, in_native_crs: bool = False) -> shapely.Polygon:
        """Translate a bounding box as a ee.Geometry polygon.

        Parameters
        ----------
        in_native_crs : bool
            Whether to use the bbox CRS (True) or WGS84 coordinates (False). Defaults to False.

        Returns
        -------
        shapely.Polygon
            The shapely polygon representing the bbox coordinates in its CRS or WGS84 (depending on `in_native_crs`).

        Warning
        -------
        Georeferencement information is lost. The shapely polygon is just a mathematical object.
        """
        bbox = self.transform(WGS84) if not in_native_crs else self
        return shapely.Polygon(
            [
                (bbox.left, bbox.top),
                (bbox.left, bbox.bottom),
                (bbox.right, bbox.bottom),
                (bbox.right, bbox.top),
                (bbox.left, bbox.top),
            ],
        )

    def to_latlon(self) -> tuple[Coordinate, Coordinate]:
        """Convert a bounding box to a tuple of the form
        (lat_min, lon_min), (lat_max, lon_max), as expected by folium.

        Returns
        -------
        (lat_min, lon_min), (lat_max, lon_max) : Coordinate, Coordinate
            Coordinates of the top right and bottom left box corners.
        """
        lon_min, lon_max = self.left, self.right
        lat_min, lat_max = self.bottom, self.top
        return ((lat_min, lon_min), (lat_max, lon_max))

    def transform(self, dst_crs: CRS) -> Self:
        """Transform a bounding box to `dst_crs`.

        If mapping to the new CRS generates distortions, the smallest box encapsulating
        the corners of the distorted box is returned. This is in general the smallest encapsulating
        box of the distorted box.

        Parameters
        ----------
        dst : CRS
            Target CRS.

        Returns
        -------
        bbox: BoundingBox
            Bounding box in `dst_crs`.
        """
        if not self.is_not_empty:
            log.warn("Transforming an empty BoundingBox")
            assert False
            return self.__class__(0, 0, 0, 0, dst_crs)
        ys, xs = zip(self.ll, self.lr, self.ul, self.ur)
        xs, ys = rio.warp.transform(self.crs, dst_crs, xs, ys)
        return self.__class__(
            left=min(xs),
            bottom=min(ys),
            right=max(xs),
            top=max(ys),
            crs=dst_crs,
        )

    def shape(self, scale: int) -> tuple[int, int]:
        """Compute the shape that would have an image at resolution `scale` fitting the bbox.

        Parameters
        ----------
        scale : int
            A pixel side-length, in meter.

        Returns
        -------
        height, width: int
        """
        _, meter_factor = self.crs.linear_units_factor
        w = meter_factor * (self.right - self.left) // scale
        h = meter_factor * (self.top - self.bottom) // scale
        return (h, w)

    @classmethod
    def from_ee_geometry(cls, geometry: ee.Geometry) -> Self:
        coordinates = np.array(geometry.bounds().getInfo()["coordinates"][0])  # type: ignore[index]
        proj = geometry.projection().getInfo()["crs"]  # type: ignore[index]
        crs = CRS.from_string(proj)
        return cls(
            left=coordinates[:, 0].min(),
            right=coordinates[:, 0].max(),
            bottom=coordinates[:, 1].min(),
            top=coordinates[:, 1].max(),
            crs=crs,
        )

    @classmethod
    def from_latlon(cls, cmin: Coordinate, cmax: Coordinate, crs: CRS = WGS84) -> Self:
        """Convert a bounding box of the form (lat_min, lon_min), (lat_max, lon_max),
        as expected by folium, to a BoundingBox.

        Parameters
        ----------
        cmin : Coordinate
            Bottom left corner coordinates.
        cmax : Coordinate
            Top right corner coordinates.
        crs : CRS (optional)
            The CRS in which the coordinates are expressed. Default is WGS84.

        Returns
        -------
        BoundingBox
        """
        return cls(left=cmin[1], right=cmax[1], bottom=cmin[0], top=cmax[0], crs=crs)

    @classmethod
    def ee_image_bbox(cls, image: ee.Image) -> Self:
        """Compute the bounding box of a GEE image in WGS84 CRS.

        Parameters
        ----------
        image : ee.Image
            A GEE image.

        Returns
        -------
        BoundingBox
        """
        coordinates = np.array(image.geometry().bounds().coordinates().getInfo())
        return cls(
            left=coordinates[:, :, 0].min(),
            right=coordinates[:, :, 0].max(),
            top=coordinates[:, :, 1].max(),
            bottom=coordinates[:, :, 1].min(),
        )

    @classmethod
    def from_rio(cls, bbox: rio.coords.BoundingBox, crs: CRS = WGS84) -> Self:
        """Get a bounding box from a `rasterio` bounding box.

        Parameters
        ----------
        bbox : rio.coords.BoundingBox
            A rasterio bounding box object.
        crs : CRS (optional)
            The CRS in which the bbox is expressed. Default is WGS84.

        Returns
        -------
        BoundingBox
        """
        return cls(
            left=bbox.left, bottom=bbox.bottom, right=bbox.right, top=bbox.top, crs=crs
        )

    @classmethod
    def from_geofile(cls, path: Path) -> Self:
        """Get a bounding box from a `rasterio`-compatible Geo file.

        Parameters
        ----------
        path : Path
            A path to a Geo file.

        Returns
        -------
        BoundingBox
            The bounding box of the geodata contained in the file.
        """
        with rio.open(path) as data:
            return cls.from_rio(data.bounds, data.crs)

    @classmethod
    def from_utm(cls, utm: UTM) -> Self:
        """Get the bounding box of a UTM zone in WGS84.

        Parameters
        ----------
        utm : UTM
            The UTM zone.

        Returns
        -------
        BoundingBox
            The bounding box expressed in WGS84.
        """
        left = (utm.zone - 31) * 6
        right = left + 6
        bottom = -80 + 8 * _UTM_ZONE_LETTERS.index(utm.letter)
        top = bottom + 8 if utm.letter != "X" else 84
        return cls(left=left, bottom=bottom, right=right, top=top)

    def to_utms(self) -> Iterator[UTM]:
        """Computes the UTM zones that the bounding box intersects."""
        bbox = self.transform(WGS84)
        zone_left = int(bbox.left // 6) + 31
        zone_right = int(bbox.right // 6) + 31
        letter_index_bottom = int((bbox.bottom + 80) // 8)
        letter_index_top = int((bbox.top + 80) // 8)
        for zone in range(zone_left, zone_right + 1):
            for letter_index in range(letter_index_bottom, letter_index_top + 1):
                yield UTM(zone, _UTM_ZONE_LETTERS[letter_index])


def close_to_utm_border(lat: float, lon: float, delta: float = 1.0) -> bool:
    """Check if the point at coordinate (lat, lon) is delta-close to a UTM border."""
    return not (delta < lon % 6 < 6 - delta)


def get_center_tif(ds: rio._base.DatasetBase) -> Coordinate:
    """Compute the center of a tif image in WGS84 CRS.

    Parameters
    ----------
    ds : rio._base.DatasetBase
        A rio dataset representing a tif image.

    Returns
    -------
    lat, lon : Coordinate
        Latitude and longitude of the center of `ds`.

    Example
    -------
    ds = rio.open("example.tif")
    m = folium.Map(location=getCenterTif(ds))
    """
    x, y = ds.xy(ds.height // 2, ds.width // 2)
    lon, lat = warp.transform(ds.crs, WGS84, [x], [y])
    return lat[0], lon[0]


def get_shape_image(image: ee.Image) -> tuple[int, int]:
    """Compute the shape of a GEE image in (width, height) format.

    Parameters
    ----------
    image : ee.Image

    Returns
    -------
    w, h : tuple[int, int]
    """
    shape: tuple[int, int] = image.getInfo()["bands"][0]["dimensions"]  # type: ignore[index]
    return shape


def get_bounding_box_tif(ds: rio._base.DatasetBase) -> tuple[Coordinate, Coordinate]:
    """Compute the bounding box of a tif image in WGS84 CRS.

    Parameters
    ----------
    ds : rio._base.DatasetBase
        A rio dataset representing a tif image.

    Returns
    -------
    (lat_min, lon_min), (lat_max, lon_max) : Coordinate, Coordinate
        Coordinates of the top right and bottom left box corners.
    """
    return BoundingBox.from_rio(ds.bounds, crs=ds.crs).transform(WGS84).to_latlon()
