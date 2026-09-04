import json
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

__all__ = [
    "ALL_SPECTRAL_INDICES",
    "CONSTANT_MAPPING",
    "LANDSAT8_MAPPING",
    "S1_MAPPING",
    "S2_MAPPING",
    "SpectralIndexItem",
]

S1_MAPPING = {
    "HH": "HH",
    "HV": "HV",
    "VV": "VV",
    "VH": "VH",
}

PALSAR2_MAPPING = {"HH": "HH", "HV": "HV"}

S2_MAPPING = {
    "A": "B1",
    "B": "B2",
    "G": "B3",
    "R": "B4",
    "RE1": "B5",
    "RE2": "B6",
    "RE3": "B7",
    "N2": "B8A",
    "N": "B8",
    "WV": "B9",
    "S1": "B11",
    "S2": "B12",
}

LANDSAT8_MAPPING = {
    "A": "SR_B1",
    "B": "SR_B2",
    "G": "SR_B3",
    "R": "SR_B4",
    "N2": "SR_B5",
    "S1": "SR_B6",
    "S2": "SR_B7",
}

CONSTANT_MAPPING = dict(
    L=1.0,
    GAIN=2.5,
    C1=6.0,
    C2=7.5,
    CEXP=1.16,
    NEXP=2.0,
    ALPHA=0.1,
    BETA=0.05,
    GAMMA=1.0,
    OMEGA=2.0,
    K=0.0,
    LAMBDAG=645.0,
    LAMBDAR=555.0,
    LAMBDAN=858.5,
    LAMBDAN2=864.7,
    LAMBDAS1=1613.7,
    LAMBDAS2=2202.4,
    SLA=1.0,
    SLB=0.0,
    SIGMA=0.5,
    P=2.0,
    C=1.0,
    FDELTA=0.581,
    EPSILON=1,
)


class SpectralIndexItem(TypedDict):
    long_name: str
    formula: str
    denominator: str | None
    reference: str
    application_domain: str
    contributor: str


class LazyAllSpectralIndices(Mapping[str, SpectralIndexItem]):
    json_data_path = Path(__file__).parent / "spectral-indices-dict.json"

    def __init__(self) -> None:
        self._all_spectral_indices: dict[str, SpectralIndexItem] | None = None

    @property
    def all_spectral_indices(self) -> dict[str, SpectralIndexItem]:
        if self._all_spectral_indices is None:
            self._all_spectral_indices = json.loads(self.json_data_path.read_text())
        return self._all_spectral_indices

    def __getitem__(self, k: str) -> SpectralIndexItem:
        ret = self.all_spectral_indices[k]
        ret["formula"] = ret["formula"].format(**CONSTANT_MAPPING)
        ret["denominator"] = (
            ret["denominator"].format(**CONSTANT_MAPPING)
            if ret["denominator"] is not None
            else None
        )
        return ret

    def __iter__(self):
        return iter(self.all_spectral_indices)

    def __len__(self):
        return len(self.all_spectral_indices)

    def __contains__(self, k):
        return k in self.all_spectral_indices


ALL_SPECTRAL_INDICES = LazyAllSpectralIndices()
