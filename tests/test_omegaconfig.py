"""Tests for union-typed config fields."""

import dataclasses
from pathlib import Path
from typing import Any

import pytest
from omegaconf import DictConfig, ListConfig, OmegaConf

from geefetch.cli.omegaconfig import (
    _UNION_ANNOTATIONS,
    UNION_FIELDS,
    AOIConfig,
    BboxAOIConfig,
    GeofileAOIConfig,
    S1Config,
    SpeckleFilterConfig,
    TerrainNormalizationConfig,
    UnionResolutionError,
    _Default,
    _resolve_config_unions,
    load,
    resolve_union,
)

SPATIAL_UNION = BboxAOIConfig | GeofileAOIConfig
COUNTRY_UNION = str | list[str] | None
SPECKLE_UNION = SpeckleFilterConfig | _Default | None


@pytest.fixture
def write_config(raw_paris_config: DictConfig | ListConfig, tmp_path: Path):
    """Return a helper that mutates the paris config and dumps it to a YAML file."""

    def _write(mutate=lambda cfg: None) -> Path:
        cfg = raw_paris_config.copy()
        cfg.data_dir = str(tmp_path / "data")
        mutate(cfg)
        path = tmp_path / "config.yaml"
        path.write_text(OmegaConf.to_yaml(cfg))
        return path

    return _write


def test_union_fields_relaxed_on_the_class():
    """Every registered field is `Any` on the class, so OmegaConf never sees the union."""
    for cls, names in UNION_FIELDS.items():
        for name in names:
            assert cls.__annotations__[name] is Any


def test_union_fields_real_annotations_are_recovered():
    """The real union hints are captured verbatim into the sidecar registry."""
    assert _UNION_ANNOTATIONS[AOIConfig]["spatial"] == SPATIAL_UNION
    assert _UNION_ANNOTATIONS[AOIConfig]["country"] == COUNTRY_UNION
    assert _UNION_ANNOTATIONS[S1Config]["speckle_filter"] == SPECKLE_UNION
    # keys stay in lockstep with UNION_FIELDS
    assert set(_UNION_ANNOTATIONS[AOIConfig]) == set(UNION_FIELDS[AOIConfig])


def test_resolve_union_spatial_bbox_branch():
    data = OmegaConf.create({"left": 1.0, "right": 2.0, "top": 4.0, "bottom": 3.0, "epsg": 2154})
    resolved = resolve_union(SPATIAL_UNION, data)
    assert isinstance(resolved, BboxAOIConfig)
    assert resolved.epsg == 2154
    assert resolved.left == 1.0


def test_resolve_union_spatial_geofile_branch(paris_geo_file):
    data = OmegaConf.create({"geofile": str(paris_geo_file)})
    resolved = resolve_union(SPATIAL_UNION, data)
    assert isinstance(resolved, GeofileAOIConfig)
    assert Path(resolved.geofile) == Path(paris_geo_file)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("France", "France"),
        (["France", "Germany"], ["France", "Germany"]),
        (None, None),
    ],
)
def test_resolve_union_country_branches(value, expected):
    data = OmegaConf.create(value) if isinstance(value, list) else value
    assert resolve_union(COUNTRY_UNION, data) == expected


def test_resolve_union_enum_sentinel_branch():
    # `_Default` is neither a dataclass nor None -> matched by the isinstance fallback
    assert resolve_union(SPECKLE_UNION, _Default.DEFAULT) is _Default.DEFAULT


def test_resolve_union_dataclass_branch():
    resolved = resolve_union(SPECKLE_UNION, OmegaConf.create({"framework": "MULTI"}))
    assert isinstance(resolved, SpeckleFilterConfig)
    assert resolved.framework == "MULTI"


def test_resolve_union_none_branch():
    # no dedicated `None` branch anymore: `isinstance(None, type(None))` in the fallback
    assert resolve_union(SPECKLE_UNION, None) is None


def test_resolve_union_spatial_mixed_branches_raises(paris_geo_file):
    """A value carrying fields from *both* union members matches neither."""
    data = OmegaConf.create({"geofile": str(paris_geo_file), "left": 1.0, "right": 2.0})
    with pytest.raises(UnionResolutionError) as excinfo:
        resolve_union(SPATIAL_UNION, data)
    message = str(excinfo.value)
    # every member is reported, with its own reason for rejecting the value
    assert "BboxAOIConfig" in message
    assert "GeofileAOIConfig" in message
    assert set(excinfo.value.errors) == {"BboxAOIConfig", "GeofileAOIConfig"}


def test_resolve_union_country_wrong_type_raises():
    with pytest.raises(UnionResolutionError):
        resolve_union(COUNTRY_UNION, 42)


def test_resolve_union_speckle_wrong_value_raises():
    with pytest.raises(UnionResolutionError):
        resolve_union(SPECKLE_UNION, "not-a-known-sentinel")


def test_load_spatial_bbox_branch(write_config):
    cfg = load(write_config())
    spatial = cfg.satellite_default.aoi.spatial
    assert isinstance(spatial, BboxAOIConfig)
    assert spatial.epsg == 2154
    # the resolved branch is propagated to every satellite section
    assert isinstance(cfg.s1.aoi.spatial, BboxAOIConfig)
    assert cfg.s1.aoi.spatial.left == 650000


def test_load_spatial_geofile_branch(write_config, paris_geo_file):
    def mutate(cfg):
        cfg.satellite_default.aoi.spatial = {"geofile": str(paris_geo_file)}

    cfg = load(write_config(mutate))
    assert isinstance(cfg.satellite_default.aoi.spatial, GeofileAOIConfig)
    assert isinstance(cfg.s2.aoi.spatial, GeofileAOIConfig)
    assert Path(cfg.s2.aoi.spatial.geofile) == Path(paris_geo_file)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("France", "France"),
        (["France", "Germany"], ["France", "Germany"]),
        (None, None),
    ],
)
def test_load_country_branches(write_config, value, expected):
    def mutate(cfg):
        cfg.satellite_default.aoi.country = value

    cfg = load(write_config(mutate))
    assert cfg.satellite_default.aoi.country == expected
    assert cfg.palsar2.aoi.country == expected


def test_load_s1_speckle_filter_none_branch(write_config):
    def mutate(cfg):
        cfg.s1.speckle_filter = None

    cfg = load(write_config(mutate))
    assert cfg.s1.speckle_filter is None


def test_load_s1_speckle_filter_dataclass_branch(write_config):
    """A user-supplied dict is resolved into a dataclass by the config walk."""

    def mutate(cfg):
        cfg.s1.speckle_filter = {"framework": "MULTI", "kernel_size": 7}

    cfg = load(write_config(mutate))
    assert isinstance(cfg.s1.speckle_filter, SpeckleFilterConfig)
    assert cfg.s1.speckle_filter.framework == "MULTI"
    assert cfg.s1.speckle_filter.kernel_size == 7
    # the other S1 union field is resolved by the same walk
    assert isinstance(cfg.s1.terrain_normalization, TerrainNormalizationConfig)


def test_load_s1_section_omitted_yields_defaults(write_config):
    """With no `s1:` section at all, both S1 unions still land on valid values."""

    def mutate(cfg):
        del cfg.s1

    cfg = load(write_config(mutate))
    assert isinstance(cfg.s1.terrain_normalization, TerrainNormalizationConfig)
    assert cfg.s1.speckle_filter is None
    # AOI unions inherited from `satellite_default` are resolved too
    assert isinstance(cfg.s1.aoi.spatial, BboxAOIConfig)
    assert cfg.s1.aoi.country == "France"


def test_load_customs_aoi_union_resolved(write_config):
    """The walk traverses `customs: dict[str, CustomSatelliteConfig]`."""
    cfg = load(write_config())
    chm = cfg.customs["chm_pauls"]
    assert isinstance(chm.aoi.spatial, BboxAOIConfig)
    assert chm.aoi.country == "France"


def test_load_does_not_leak_default_sentinel(write_config):
    """`_post_omegaconf_load` must expand every `_Default` before the walk runs."""
    cfg = load(write_config())
    assert cfg.s1.terrain_normalization not in (_Default.DEFAULT, "default")
    assert isinstance(cfg.s1.terrain_normalization, TerrainNormalizationConfig)
    assert cfg.s1.speckle_filter is None or isinstance(cfg.s1.speckle_filter, SpeckleFilterConfig)


def test_load_s1_terrain_normalization_default_string(write_config):
    """A YAML-provided `default` string expands to a baseline config."""

    def mutate(cfg):
        cfg.s1.terrain_normalization = "default"

    cfg = load(write_config(mutate))
    assert isinstance(cfg.s1.terrain_normalization, TerrainNormalizationConfig)


def test_load_s1_terrain_normalization_default_sentinel(write_config):
    """Omitting the field falls back to the `_Default.DEFAULT` dataclass default."""

    def mutate(cfg):
        del cfg.s1.terrain_normalization

    cfg = load(write_config(mutate))
    assert isinstance(cfg.s1.terrain_normalization, TerrainNormalizationConfig)


def test_load_spatial_mixed_branches_raises(write_config, paris_geo_file):
    def mutate(cfg):
        cfg.satellite_default.aoi.spatial = {
            "geofile": str(paris_geo_file),
            "left": 650000,
            "right": 650001,
        }

    with pytest.raises(UnionResolutionError) as excinfo:
        load(write_config(mutate))
    message = str(excinfo.value)
    assert "BboxAOIConfig" in message
    assert "GeofileAOIConfig" in message


def test_load_spatial_unknown_field_raises(write_config):
    """A bbox-shaped value with a stray key belongs to neither branch."""

    def mutate(cfg):
        cfg.satellite_default.aoi.spatial.not_a_real_field = 1

    with pytest.raises(UnionResolutionError):
        load(write_config(mutate))


def test_load_country_wrong_type_raises(write_config):
    def mutate(cfg):
        cfg.satellite_default.aoi.country = 42

    with pytest.raises(UnionResolutionError):
        load(write_config(mutate))


def test_resolve_config_unions_walks_dict_and_list():
    """The walk reaches registered nodes nested inside `dict` values and `list` items."""

    def make_aoi() -> AOIConfig:
        return AOIConfig(
            spatial={
                "left": 1.0,
                "right": 2.0,
                "top": 4.0,
                "bottom": 3.0,
                "epsg": 2154,
            },  # ty:ignore[invalid-argument-type]
            temporal=None,
            country="France",
        )

    @dataclasses.dataclass
    class _Root:
        in_dict: dict
        in_list: list

    nested_dict = make_aoi()
    nested_list = make_aoi()
    _resolve_config_unions(_Root(in_dict={"a": nested_dict}, in_list=[nested_list]))

    for aoi in (nested_dict, nested_list):
        assert isinstance(aoi.spatial, BboxAOIConfig)
        assert aoi.spatial.epsg == 2154
        assert aoi.country == "France"
