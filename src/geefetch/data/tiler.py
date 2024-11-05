import logging
import re
from math import ceil, floor
from pathlib import Path
from typing import Callable, Iterator, Optional

import rasterio as rio
import shapely
from geobbox import UTM, GeoBoundingBox
from rasterio.crs import CRS

from ..utils.enums import Format
from ..utils.rasterio import WGS84
from .satellites import SatelliteABC

log = logging.getLogger(__name__)

__all__ = ["Tiler", "TileTracker"]


class MaximumIterationError(Exception):
    pass


MAX_TILE_LIMIT = 100_000_000


class Tiler:
    """
    The class for handling splitting a region into non-overlapping smaller tiles.
    """

    _SUBTILE_DEGREE_SIZE = 0.3

    def _multiple_below(self, x: float | int, m: int) -> int:
        return m * int(floor(x / m))

    def _multiple_above(self, x: float | int, m: int) -> int:
        return m * int(ceil(x / m))

    def is_on_distortion_overlap(self, bbox: GeoBoundingBox) -> bool:
        """Determines if `bbox` is on a tile overlap, because of the way the Tiler splits large areas.

        Parameters
        ----------
        bbox: GeoBoundingBox
            The bbox to check for overlap.

        Returns
        -------
        bool
            When True, the point may be included in several tiles. When False, the point is guaranteed not to lie
            on an overlap.
        """
        for latlon in [bbox.ul, bbox.ur, bbox.ll, bbox.lr]:
            lat, lon = latlon
            if abs(lon - 6 * (lon // 6)) < 0.1:
                # close to a UTM border
                return True
            if abs(lat) < 0.01:
                # close to the equator
                return True
        return False

    def _split_in_grid(
        self, bbox: GeoBoundingBox, shape: int
    ) -> Iterator[GeoBoundingBox]:
        count = 0
        for left in range(
            self._multiple_below(bbox.left, shape),
            self._multiple_above(bbox.right, shape),
            shape,
        ):
            for bottom in range(
                self._multiple_below(bbox.bottom, shape),
                self._multiple_above(bbox.top, shape),
                shape,
            ):
                yield GeoBoundingBox(
                    left=left,
                    bottom=bottom,
                    right=left + shape,
                    top=bottom + shape,
                    crs=bbox.crs,
                )
                count += 1
                if count > MAX_TILE_LIMIT:
                    raise MaximumIterationError(
                        f"AOI is split in more than {MAX_TILE_LIMIT} tiles. This may be caused by CRS distortion."
                    )

    def split(
        self,
        aoi: GeoBoundingBox,
        shape: int,
        crs: Optional[CRS] = None,
        filter_polygon: Optional[shapely.Polygon] = None,
    ) -> Iterator[GeoBoundingBox]:
        """Split a region into non-overlapping tiles having shape `shape`x`shape`.

        Parameters
        ----------
        aoi : GeoBoundingBox
            The area of interest.
        shape : int
            The desired side length for tiles (in meters).
        crs : Optional[CRS], optional
            The CRS in which to download data. If None, AOI is split in UTM zones and
            data is downloaded in their local UTM zones. Defaults to None.
        filter_polygon : shapely.Polygon, optional
            If given, only yields tiles which WGS84 bounding boxes intersect the polygon.

        Returns
        -------
        List[GeoBoundingBox]
        """
        if crs is not None and crs.units_factor[0] != "metre":
            log.warn("Using a tiler with non-metric CRS.")

        skip_count = 0

        if crs is not None:
            bbox = aoi.transform(crs)
            for bbox in self._split_in_grid(aoi.transform(crs), shape):
                bbox84 = bbox.transform(WGS84)
                if filter_polygon is None or filter_polygon.intersects(
                    bbox84.to_shapely_polygon()
                ):
                    yield bbox
                else:
                    skip_count += 1
        else:
            for utm in aoi.to_utms():
                log.debug(f"AOI intersects UTM zone {utm}.")
                utm_bbox = GeoBoundingBox.from_utm(utm) & aoi.transform(WGS84)
                for bbox in self._split_in_grid(utm_bbox.transform(utm.crs), shape):
                    bbox84 = bbox.transform(WGS84)
                    if bbox84.intersects(utm_bbox):
                        if filter_polygon is None or filter_polygon.intersects(
                            bbox84.to_shapely_polygon()
                        ):
                            yield bbox
                        else:
                            skip_count += 1
        log.debug(
            f"Skipped {skip_count} tiles that did not intersect the country polygon."
        )


class TileTracker:
    """
    The class for handling the interface between data and physical locations in the filesystem.
    """

    def __init__(
        self,
        satellite: SatelliteABC,
        project_dir: Path,
        sub_root: Optional[str] = None,
        filter: Optional[Callable[[Path], bool] | str] = None,
    ):
        self._satellite = satellite
        self.project_dir = project_dir
        self.sub_root = sub_root
        self._filter = filter
        if self._filter is None and satellite.is_raster:
            self._filter = r".*\.tif"
        if not self.root.exists():
            self.root.mkdir(parents=True)
            log.debug(f"Created data directory {self.root}")

    @property
    def root(self) -> Path:
        """The root directory where data is stored."""
        if self.sub_root is not None:
            return self.project_dir / self.satellite.name / self.sub_root
        return self.project_dir / self.satellite.name

    @property
    def satellite(self) -> SatelliteABC:
        """The satellite associated to the data that the dataset handles."""
        return self._satellite

    def name_crs(self, crs: CRS) -> str:
        if UTM.is_utm_crs(crs):
            ret: str = UTM.utm_strip_name_from_crs(crs)
            return ret
        return f"EPSG{crs.to_epsg()}"

    def get_path(self, bbox: GeoBoundingBox, format: Optional[Format] = None) -> Path:
        tile_suffix = (
            ".tif"
            if self.satellite.is_raster
            else ".geojson" if format is None else format.value
        )
        tile_stem = f"{self.satellite.name}_{self.name_crs(bbox.crs)}_{bbox.left:.0f}_{bbox.bottom:.0f}"
        tile_path = self.root / (tile_stem + tile_suffix)
        if not self.filter(tile_path):
            raise RuntimeError(
                f"{self.__class__.__name__} created path {tile_path} that is not accepted by its filter."
            )
        return tile_path

    @classmethod
    def tile_id_from_filename(cls, path: Path) -> str:
        """Determine a bounding box identifier of a georeferenced file based on its name.
        Useful to match file using the file names instead of trusting the georeferenced meta info.

        Fails if the filename was not generated using a TileTracker."""
        id_re = r".*_(?P<tile_id>.*_\d*_\d*).*"
        match = re.match(id_re, path.name)
        if match is None:
            raise ValueError(f"Could not infer tile_id from {path.name}")
        return match["tile_id"]

    @classmethod
    def satellite_from_filename(cls, path: Path) -> str:
        """Determine a bounding box identifier of a georeferenced file based on its name.
        Useful to match file using the file names instead of trusting the georeferenced meta info.

        Fails if the filename was not generated using a TileTracker."""
        satellite_re = r"(?P<satellite>.*)_(.*_\d*_\d*)\..*"
        match = re.match(satellite_re, path.name)
        if match is None:
            raise ValueError(f"Could not infer satelitte from {path.name}")
        return match["satellite"]

    def filter(self, file: Path) -> bool:
        if file.stem.startswith("._"):
            return False
        if self._filter is None:
            return True
        if isinstance(self._filter, str):
            return re.fullmatch(self._filter, str(file)) is not None
        return self._filter(file)

    def __iter__(self) -> Iterator[Path]:
        for path in self.root.rglob("*"):
            if self.filter(path):
                yield path

    def crs_to_paths(self) -> dict[CRS, list[Path]]:
        ret: dict[CRS, list[Path]] = {}
        for path in self:
            with rio.open(path) as ds:
                meta = ds.meta
            crs = meta["crs"]
            if crs not in ret:
                ret[crs] = []
            ret[crs].append(path)
        return ret

    def __str__(self) -> str:
        return f"Tracker({self.root})"
