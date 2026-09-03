import logging
from dataclasses import dataclass
from typing import cast

import ee
from ee.image import Image
from ee.imagecollection import ImageCollection

from ...cli.omegaconfig import SatelliteDefaultConfig
from .enums import IndeciesExpressions

log = logging.getLogger(__name__)

EXPRESSION_BANDS = [
    "HH",
    "HV",
    "VV",
    "VH",
    "A",
    "B",
    "G",
    "R",
    "RE1",
    "RE2",
    "RE3",
    "N2",
    "N",
    "WV",
    "S1",
    "S2",
]


@dataclass(frozen=True)
class SpectralIndex:
    name: str
    expression: str
    expression_bands: list[str]
    expression_denominator: str | None
    band_mapping: dict[str, str]

    def _has_required_bands(self, image: Image) -> ee.Number:
        # In case an Image is missing a Band, this boolean will trigger the return of an empty band.
        required_bands_ee = ee.List([self.band_mapping.get(band) for band in self.expression_bands])
        present = image.bandNames()
        return required_bands_ee.removeAll(present).size().eq(0)

    def _add_index_to_image(self, image: Image) -> Image:
        """Adds a spectral index band to a given Image."""

        def _add() -> Image:
            bands = {key: image.select(value) for key, value in self.band_mapping.items()}
            out = image.expression(expression=self.expression, map_=bands).rename(self.name)
            if self.expression_denominator:
                denominator_mask = image.expression(
                    expression=self.expression_denominator, map_=bands
                )
                out.updateMask(denominator_mask.neq(0))
            return image.addBands(out)

        def _empty() -> Image:
            empty_spectral_index: Image = (
                Image.constant(0).updateMask(0).reproject(image.select(0).projection())
            ).rename(self.name)
            return image.addBands(empty_spectral_index)

        out: Image = ee.Algorithms.If(self._has_required_bands(image), _add(), _empty())
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
    """Reads through a given configuration object and produces a list of SpectralIndex to be"""
    spectral_indices: list[SpectralIndex] | None = None
    if config.spectral_indices:
        spectral_indices = []
        for spectral_index_name in config.spectral_indices:
            if spectral_index_name not in IndeciesExpressions._member_names_:
                msg = f"""
                    {spectral_index_name} does not figure in the list of GeeFetch
                    implemented spectral indices.\n
                    Ask a maintainer to add it or do it yourself. Aborting.
                """
                log.error(msg)
                raise ValueError(msg)
            else:
                spectral_index = IndeciesExpressions[spectral_index_name]
                expression = spectral_index.value.get("formula", "")
                expression_bands = [band for band in EXPRESSION_BANDS if band in expression]

                missing_bands_from_mapping = [
                    band for band in expression_bands if band not in mapping
                ]

                if missing_bands_from_mapping:
                    # Do not initialize the SpectralIndex if any of the bands used
                    # in the expression are missing from the sensor band mapping.
                    msg = f"""
                        {spectral_index_name} won't be calculated as the following bands do not
                        figure in the sensor band mapping: {missing_bands_from_mapping}.
                    """
                    log.warning(msg)

                else:
                    spectral_indices.append(
                        SpectralIndex(
                            name=spectral_index.name,
                            expression=expression,
                            expression_bands=expression_bands,
                            expression_denominator=spectral_index.value.get("denominator"),
                            band_mapping=mapping,
                        )
                    )
    return spectral_indices
