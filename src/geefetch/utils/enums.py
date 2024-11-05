"""The Enum types used in geefetch."""

from enum import Enum

import ee


class DType(Enum):
    """The data type for downloaded data."""

    UInt8 = "UINT8"
    UInt16 = "UINT16"
    Float32 = "FLOAT32"
    Float64 = "FLOAT64"

    def transform(self, im: ee.Image) -> ee.Image:
        match self:
            case DType.UInt8:
                return im.toUint8()
            case DType.UInt16:
                return im.toUint16()
            case DType.Float32:
                return im.toFloat()
            case DType.Float64:
                raise TypeError("Google Earth Engine does not allow float64 data type.")
            case _:
                raise ValueError(f"Unknown dtype {self.value}.")

    def to_str(self) -> str:
        return self.value.lower()


class CompositeMethod(Enum):
    """The composite method for multiple images mosaicking."""

    MEAN = "MEAN"
    MEDIAN = "MEDIAN"
    MEDOID = "MEDOID"
    MOSAIC = "MOSAIC"
    TIMESERIES = "TIME_SERIES"

    def transform(self, col: ee.ImageCollection) -> ee.Image:
        match self:
            case CompositeMethod.MEAN:
                return col.mean()
            case CompositeMethod.MEDIAN:
                return col.median()
            case CompositeMethod.MEDOID:
                raise ValueError(
                    "Google Earth Engine does not provide medoid composite."
                )
            case CompositeMethod.MOSAIC:
                return col.mosaic()
            case CompositeMethod.TIMESERIES:
                raise RuntimeError(
                    f"Cannot composite for composite method {CompositeMethod.TIMESERIES}"
                )
            case _:
                raise ValueError(f"Unknown composite method {self.value}.")


class Format(Enum):
    """The file format for downloaded vector data."""

    CSV = ".csv"
    GEOJSON = ".geojson"
    KML = ".kml"
    KMZ = ".kmz"
    PARQUET = ".parquet"

    def to_str(self) -> str:
        match self:
            case Format.CSV:
                return "csv"
            case Format.GEOJSON:
                return "geojson"
            case Format.KML:
                return "kml"
            case Format.KMZ:
                return "kmz"
            case Format.PARQUET:
                return "parquet"
