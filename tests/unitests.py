from unittest.mock import patch

import pytest
import rasterio.warp as warp
import shapely
from geobbox import GeoBoundingBox
from rasterio.crs import CRS

from geefetch.data.tiler import Tiler

# Define a variety of bounding boxes and their corresponding tiling sizes
BBOXES_AND_SHAPES = [
    (
        GeoBoundingBox(left=500000, bottom=0, right=510000, top=10000, crs=CRS.from_epsg(32633)),
        5000,
    ),  # UTM33N, 5km
    (
        GeoBoundingBox(left=400000, bottom=0, right=420000, top=20000, crs=CRS.from_epsg(32632)),
        10000,
    ),  # UTM32N, 10km
    (
        GeoBoundingBox(left=-10, bottom=-10, right=10, top=10, crs=CRS.from_epsg(4326)),
        111000,
    ),  # WGS84, ~111km per degree
    (
        GeoBoundingBox(left=-5, bottom=-1, right=5, top=1, crs=CRS.from_epsg(4326)),
        55500,
    ),  # Overlapping equator, ~55.5km per 0.5°
    (
        GeoBoundingBox(left=-3, bottom=0, right=9, top=5, crs=CRS.from_epsg(4326)),
        111000,
    ),  # Multi-UTM, ~111km per degree
    (
        GeoBoundingBox(left=500000, bottom=0, right=550000, top=50000, crs=CRS.from_epsg(32633)),
        10000,
    ),  # Large UTM region, 10km tiles
]
BBOXES_AND_SHAPES_IDS = [
    "UTM33N_5km",
    "UTM32N_10km",
    "WGS84_111km",
    "Equator_Overlap_55km",
    "Multi_UTM_111km",
    "Large_UTM_10km",
]


@pytest.fixture
def simple_bbox() -> GeoBoundingBox:
    """Fixture for a sample AOI covering a small area."""
    return GeoBoundingBox(
        left=500000, bottom=0, right=510000, top=10000, crs=CRS.from_epsg(32633)
    )  # UTM33N


def assert_non_overlapping(tiles: list[GeoBoundingBox]):
    """Assert that no two tiles overlap, but only compare tiles with the same CRS."""
    for i, b1 in enumerate(tiles[:-1]):
        for b2 in tiles[i + 1 :]:
            if b1.crs != b2.crs:
                continue
            assert (b1 & b2).is_empty, f"Tiles {b1} and {b2} should not overlap"


@pytest.mark.parametrize(("sample_bbox", "shape"), BBOXES_AND_SHAPES, ids=BBOXES_AND_SHAPES_IDS)
def test_split_in_given_crs(sample_bbox: GeoBoundingBox, shape: int):
    """Test basic splitting into tiles of a given shape."""
    tiler = Tiler()
    tiles = list(tiler.split(sample_bbox, shape, crs=sample_bbox.crs))

    for tile in tiles:
        assert tile.crs == sample_bbox.crs
        assert tile.right - tile.left == shape
        assert tile.top - tile.bottom == shape

    assert_non_overlapping(tiles)


@pytest.mark.parametrize(("sample_bbox", "shape"), BBOXES_AND_SHAPES, ids=BBOXES_AND_SHAPES_IDS)
def test_split_in_utm_crs(sample_bbox: GeoBoundingBox, shape: int):
    """Test that split respects UTM zones when no CRS is explicitly provided."""
    tiler = Tiler()
    tiles = list(tiler.split(sample_bbox, shape, crs=None))

    assert len(tiles) > 0
    for tile in tiles:
        assert tile.right - tile.left == shape
        assert tile.top - tile.bottom == shape

    assert_non_overlapping(tiles)


def test_split_warns_for_non_metric_crs(simple_bbox: GeoBoundingBox):
    """Ensure a warning is logged when using a non-metric CRS."""
    tiler = Tiler()
    shape = 5000  # 5km tiles
    non_metric_crs = CRS.from_epsg(4326)  # WGS 84 (degrees)

    with patch("geefetch.data.tiler.log.warning") as mock_warn:
        tiles = list(tiler.split(simple_bbox, shape, crs=non_metric_crs))
        mock_warn.assert_called_with("Using a tiler with non-metric CRS.")

    assert_non_overlapping(tiles)


def test_split_with_filter_polygon(simple_bbox: GeoBoundingBox):
    """Test that only tiles intersecting a filter polygon are returned."""
    tiler = Tiler()
    shape = 5000
    filter_polygon = shapely.box(506000, 2000, 508000, 7000)  # A smaller sub-region
    filter_polygon_dense = shapely.segmentize(filter_polygon, max_segment_length=5_400 / 21)
    filter_polygon_wgs84 = shapely.geometry.shape(
        warp.transform_geom(simple_bbox.crs, CRS.from_epsg(4326), filter_polygon_dense)
    )

    tiles = list(
        tiler.split(simple_bbox, shape, crs=simple_bbox.crs, filter_polygon=filter_polygon_wgs84)
    )

    assert len(tiles) == 2
    for tile in tiles:
        assert shapely.box(tile.left, tile.bottom, tile.right, tile.top).intersects(filter_polygon)

    assert_non_overlapping(tiles)


def test_split_uses_utm_if_no_crs_given(simple_bbox: GeoBoundingBox):
    """Test that split respects UTM zones when no CRS is explicitly provided."""
    tiler = Tiler()
    shape = 5000
    tiles = list(tiler.split(simple_bbox, shape, crs=None))

    assert len(tiles) > 0
    for tile in tiles:
        assert tile.crs.to_epsg() in [32633]  # Expected UTM zone for the given bbox

    assert_non_overlapping(tiles)
