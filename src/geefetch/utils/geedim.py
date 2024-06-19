import rasterio as rio
from rasterio.crs import CRS
from shapely import Polygon


def bounds_to_polygon(left: float, bottom: float, right: float, top: float) -> Polygon:
    return Polygon(
        [
            (left, top),
            (left, bottom),
            (right, bottom),
            (right, top),
            (left, top),
        ],
    )


def transform_polygon(polygon: Polygon, src_crs: CRS, dst_crs: CRS) -> Polygon:
    xs, ys = rio.warp.transform(src_crs, dst_crs, *polygon.exterior.xy)
    return Polygon(zip(xs, ys))
