import logging
from dataclasses import dataclass
from enum import Enum
from typing import cast

import ee
from ee.image import Image
from ee.imagecollection import ImageCollection

from ..cli.omegaconfig import SatelliteDefaultConfig

log = logging.getLogger(__name__)


class VegetationIndeciesExpressions(Enum):
    NDVI = {"expression": "(NIR - RED) / (NIR + RED)", "denominator": "(NIR + RED)"}
    NBR = {"expression": "(NIR - SWIR2) / (NIR + SWIR2)", "denominator": "(NIR + SWIR2)"}


S2_MAPPING = {"RED": "B4", "GREEN": "B3", "BLUE": "B2", "SWIR2": "B12", "NIR": "B8"}


@dataclass(frozen=True)
class SpectralIndex:
    name: str
    expression: str | None
    expression_denominator: str | None
    band_mapping: dict[str, str]

    def _add_index_to_image(self, image: Image) -> Image:
        """Adds a spectral index band to a given Image."""
        bands = {key: image.select(value) for key, value in self.band_mapping.items()}
        required_bands = ee.List(list(self.band_mapping.values()))
        present = image.bandNames()

        has_required_bands = required_bands.removeAll(present).size().eq(0)

        def _add() -> Image:
            out = image.expression(expression=self.expression, map_=bands).rename(self.name)
            if self.expression_denominator:
                denominator_mask = image.expression(
                    expression=self.expression_denominator, map_=bands
                )
                out.updateMask(denominator_mask.neq(0))
            return image.addBands(out)

        def _empty() -> Image:
            empty_spectral_index: Image = (
                Image.constant(0).updateMask(0).rename(self.name).reproject(image.projection())
            )
            return empty_spectral_index

        out: Image = ee.Algorithms.If(has_required_bands, _add(), _empty())
        return out

    def add_spectral_index_band_to_image_collection(
        self, image_collection: ImageCollection
    ) -> ImageCollection:
        """Adds a spectral index Band to a given Image Collection.

        Parameters
        ----------
        image_collection : ImageCollection
            Image Collection to which will be added the spectral index band.

        Returns
        -------
        ImageCollection
            The input ImageCollection with Images containing a new band that
            coresponds to the expression defined by the spectral_index.
        """
        if not self.expression:
            msg = f"""
                Expression not found for {self.name}.
                Verify documentation to ensure the index is implemented.
            """
            log.error(msg)
            raise ValueError(msg)
        return cast(
            ImageCollection, image_collection.map(lambda img: self._add_index_to_image(img))
        )


def load_spectral_indices_from_conf(
    config: SatelliteDefaultConfig, mapping: dict[str, str]
) -> list[SpectralIndex] | None:
    spectral_indices: list[SpectralIndex] | None = None
    if config.spectral_indices:
        spectral_indices = []
        for spectral_index_name in config.spectral_indices:
            if spectral_index_name not in VegetationIndeciesExpressions._member_names_:
                msg = f"""
                    {spectral_index_name} does not figure in the list of GeeFetch
                    implemented spectral indices.\n
                    Ask a maintainer to add it or do it yourself. Aborting.
                """
                log.error(msg)
                raise ValueError(msg)
            else:
                spectral_index = VegetationIndeciesExpressions[spectral_index_name]
                spectral_indices.append(
                    SpectralIndex(
                        name=spectral_index.name,
                        expression=spectral_index.value.get("expression"),
                        expression_denominator=spectral_index.value.get("denominator"),
                        band_mapping=mapping,
                    )
                )
    return spectral_indices
