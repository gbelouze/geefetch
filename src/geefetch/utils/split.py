import math
from collections.abc import Iterator
from typing import TypeVar

from geobbox import GeoBoundingBox

_T = TypeVar("_T")


def as_resolution_tuple(resolution: _T | tuple[_T, _T]) -> tuple[_T, _T]:
    if not isinstance(resolution, tuple) and resolution is not None:
        return (resolution, resolution)
    return resolution


def _floor_resolution_grid(z: float, grid: int) -> int:
    return grid * int(z // grid)


def _ceil_resolution_grid(z: float, grid: int) -> int:
    return grid * math.ceil(z / grid)


def snap_to_grid(bbox: GeoBoundingBox, grid: int | tuple[int, int]) -> GeoBoundingBox:
    """'Snap' the bounding box so that its bounds aligns with a given grid.

    The returned bounding box is guaranteed to contain the original bounding box.

    Parameters
    ----------
    bbox : GeoBoundingBox
    grid : int | tuple[int, int]
        Defines x_grid, y_grid to snap the x- and y-coordinates of the bbox to.

    Returns
    -------
    GeoBoundingBox
        The bounding box inflated to snap to the grid.

    """
    xgrid, ygrid = as_resolution_tuple(grid)
    return bbox.with_(
        left=_floor_resolution_grid(bbox.left, xgrid),
        right=_ceil_resolution_grid(bbox.right, xgrid),
        bottom=_floor_resolution_grid(bbox.bottom, ygrid),
        top=_ceil_resolution_grid(bbox.top, ygrid),
    )


def approximate_split(
    bbox: GeoBoundingBox, minimal_size: float, resolution_grid: int | tuple[int, int] | None = None
) -> Iterator[GeoBoundingBox]:
    """Splits a bounding box into a grid of non-overlapping sub-bounding boxes of equal size.

    Parameters
    ----------
    bbox : GeoBoundingBox
        The bounding box to be split.
    minimal_size : float
        The minimum side length for each sub-bounding box, in box coordinates.
    resolution_grid : int | tuple[int, int] | None
        If provided, ensures that the sub-bounding box boundaries are aligned to the nearest
        multiple of this value.

    Yields
    ------
    GeoBoundingBox
        The generated sub-bounding boxes, adjusted based on `resolution_grid` if applicable.

    Notes
    -----
    if `resolution_grid` is provided, the resulting grid may be bigger than the original `bbox`.
    """
    resolution_grid = as_resolution_tuple(resolution_grid) if resolution_grid is not None else None

    if resolution_grid is not None:
        bbox = snap_to_grid(bbox, resolution_grid)
        stridex: int | float = _ceil_resolution_grid(minimal_size, resolution_grid[0])
        stridey: int | float = _ceil_resolution_grid(minimal_size, resolution_grid[1])
        nx_split = max(1, int((bbox.right - bbox.left) // stridex))
        ny_split = max(1, int((bbox.top - bbox.bottom) // stridey))
    else:
        nx_split = max(1, int((bbox.right - bbox.left) // minimal_size))
        ny_split = max(1, int((bbox.top - bbox.bottom) // minimal_size))
        stridex = (bbox.right - bbox.left) / nx_split
        stridey = (bbox.top - bbox.bottom) / ny_split

    for x in range(nx_split):
        for y in range(ny_split):
            yield GeoBoundingBox(
                left=bbox.left + x * stridex,
                right=bbox.left + (x + 1) * stridex,
                bottom=bbox.bottom + y * stridey,
                top=bbox.bottom + (y + 1) * stridey,
                crs=bbox.crs,
            )
