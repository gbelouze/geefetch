"""Google Earth Engine utilities."""

from enum import Enum

import ee


def auth(project: str) -> None:
    """Authentificate and initialize Google Earth Engine

    Parameters
    ----------
    project : str
        Google Earth Engine project id.
    """
    ee.Authenticate(auth_mode="appdefault")
    ee.Initialize(
        project=project,
        opt_url="https://earthengine-highvolume.googleapis.com",
    )


class DType(Enum):
    UInt16 = "UINT16"
    Float32 = "FLOAT32"
    Float64 = "FLOAT64"

    def transform(self, im: ee.Image) -> ee.Image:
        match self:
            case DType.UInt16:
                return im.toUint16()
            case DType.Float32:
                return im.toFloat32()
            case DType.Float64:
                return im.toFloat64()
            case _:
                raise ValueError(f"Unknown dtype {self.value}.")

    def to_str(self) -> str:
        return self.value.lower()


class CompositeMethod(Enum):
    MEAN = "MEAN"
    MEDIAN = "MEDIAN"
    MEDOID = "MEDOID"
    MOSAIC = "MOSAIC"

    def transform(self, col: ee.ImageCollection) -> ee.Image:
        match self:
            case CompositeMethod.MEAN:
                return col.mean()
            case CompositeMethod.MEDIAN:
                return col.median()
            case CompositeMethod.MEDOID:
                return col.medoid()
            case CompositeMethod.MOSAIC:
                return col.mosaic()
            case _:
                raise ValueError(f"Unknown composite method {self.value}.")


class Format(Enum):
    CSV = ".csv"
    GEOJSON = ".geojson"
    KML = ".kml"
    KMZ = ".kmz"

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
