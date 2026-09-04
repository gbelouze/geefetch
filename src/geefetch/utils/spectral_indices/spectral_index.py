import logging
import re
from dataclasses import dataclass
from typing import cast

import ee
from ee.image import Image
from ee.imagecollection import ImageCollection

from ...utils.enums import DType
from .enums import ALL_SPECTRAL_INDEX_RANGES, ALL_SPECTRAL_INDICES

log = logging.getLogger(__name__)

# Matches whole identifier-like tokens in a formula, e.g. picks out "N" from "N + 1" but
# not from "N2" -- used to detect which of EXPRESSION_BANDS a formula actually references,
# rather than a substring check (which would e.g. treat "N" as present in "N2").
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")

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
    pixel_range: tuple[float, float] | None = None

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
            if self.expression_denominator is not None:
                denominator_mask = image.expression(
                    expression=self.expression_denominator, map_=bands
                )
                out = out.updateMask(denominator_mask.neq(0))
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

        return cast(ImageCollection, image_collection.map(self._add_index_to_image))


def load_spectral_indices_from_conf(
    spectral_index_names: list[str] | None,
    mapping: dict[str, str],
    dtype: DType,
) -> list[SpectralIndex] | None:
    """Reads through a satellite configuration and produces a list of requested spectral indices.

    Parameters
    ----------
    spectral_index_names : list[str] | None
        Some satellite configured spectral indices.
    mapping : dict[str, str]
        Mapping of spectral expression to band name. This explains which band is red, which band
        is NIR, etc.
    dtype : DType
        The dtype the satellite images will be converted to. An index with no known value
        range (see `ALL_SPECTRAL_INDEX_RANGES`) can only be requested when `dtype` is
        `DType.Float32`, since rescaling to an integer dtype requires a known range.

    Returns
    -------
    list[SpectralIndex] | None
        The requested spectral indices, or None if none are configured.

    """
    if spectral_index_names is None:
        return None

    spectral_indices = []
    for spectral_index_name in spectral_index_names:
        if spectral_index_name not in ALL_SPECTRAL_INDICES:
            msg = f"""
                {spectral_index_name} does not figure in the list of GeeFetch
                implemented spectral indices.\n
                Ask a maintainer to add it or do it yourself. Aborting.
            """
            log.error(msg)
            raise ValueError(msg)

        spectral_index = ALL_SPECTRAL_INDICES[spectral_index_name]
        expression = spectral_index["formula"]

        expression_tokens = set(_TOKEN_RE.findall(expression))
        expression_bands = [band for band in EXPRESSION_BANDS if band in expression_tokens]
        missing_bands_from_mapping = [band for band in expression_bands if band not in mapping]

        if missing_bands_from_mapping:
            # Do not initialize the SpectralIndex if any of the bands used
            # in the expression are missing from the sensor band mapping.
            msg = f"""
                {spectral_index_name} won't be calculated as the following bands do not
                figure in the sensor band mapping: {missing_bands_from_mapping}.
            """
            log.warning(msg)
            continue

        pixel_range = ALL_SPECTRAL_INDEX_RANGES.get(spectral_index_name)
        if pixel_range is None and dtype != DType.Float32:
            msg = (
                f"Spectral index {spectral_index_name} has no known value range, so it "
                f"cannot be converted to {dtype}. Use `dtype: float32`, or pick a spectral "
                "index with a known range (see spectral-index-ranges.json)."
            )
            log.error(msg)
            raise ValueError(msg)

        spectral_indices.append(
            SpectralIndex(
                name=spectral_index_name,
                expression=expression,
                expression_bands=expression_bands,
                expression_denominator=spectral_index["denominator"],
                band_mapping=mapping,
                pixel_range=pixel_range,
            )
        )
    return spectral_indices
