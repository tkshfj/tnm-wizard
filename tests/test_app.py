"""Tests for critical backend logic in app.py."""
from __future__ import annotations

import pytest

from app import (
    OrganConfig,
    _pick_primary_row,
    build_histologic_summary,
    build_nodal_summary,
    derive_stage,
    extract_fields,
    getlist,
    normalize_tnm_component,
    parse_pct,
    to_bool,
    to_float_or_none,
)


# ---------------------------------------------------------------------------
# Fixtures – minimal OrganConfig objects
# ---------------------------------------------------------------------------
@pytest.fixture()
def lung_cfg() -> OrganConfig:
    """Real lung config loaded from YAML (integration-style)."""
    from app import FORM_CONFIGS

    return FORM_CONFIGS["lung"]


@pytest.fixture()
def mini_cfg() -> OrganConfig:
    """Tiny config with a histologic_mix field for unit tests."""
    return OrganConfig(
        organ="test",
        display_name="Test",
        version="v1",
        sections=[
            {
                "id": "basic",
                "fields": [
                    {"name": "color", "type": "radio"},
                    {"name": "size", "type": "number"},
                    {"name": "flag", "type": "checkbox"},
                    {"name": "toppings", "type": "checkbox", "options": [
                        {"code": "A"}, {"code": "B"}, {"code": "C"},
                    ]},
                    {"name": "note", "type": "text"},
                ],
            }
        ],
        template="dummy.j2",
        stage_table={
            "T1a,N0,M0": "Stage IA1",
            "T1b,N0,M0": "Stage IA2",
            "T2a,N1,M0": "Stage IIB",
            "T*,N*,M1a": "Stage IVA",
            "T*,N*,M1c*": "Stage IVB",
        },
    )


@pytest.fixture()
def mix_cfg() -> OrganConfig:
    """Config with a histologic_mix field for histology summary tests."""
    return OrganConfig(
        organ="mix_test",
        display_name="Mix Test",
        version="v1",
        sections=[
            {
                "id": "histo",
                "fields": [
                    {
                        "name": "histologic_mix",
                        "type": "histologic_mix",
                        "rows": 4,
                        "types": [
                            {
                                "code": "AD",
                                "label": "Invasive non-mucinous adenocarcinoma",
                                "subtypes": [
                                    {"code": "AD_lepidic", "label": "lepidic"},
                                    {"code": "AD_acinar", "label": "conventional acinar"},
                                    {"code": "AD_solid", "label": "solid"},
                                ],
                            },
                            {
                                "code": "SQ",
                                "label": "Squamous cell carcinoma",
                                "subtypes": [
                                    {"code": "SQ_keratin", "label": "Squamous cell carcinoma, keratinizing type"},
                                ],
                            },
                        ],
                    },
                ],
            }
        ],
        template="dummy.j2",
        stage_table={},
    )


@pytest.fixture()
def no_mix_cfg() -> OrganConfig:
    """Config WITHOUT a histologic_mix field."""
    return OrganConfig(
        organ="no_mix",
        display_name="No Mix",
        version="v1",
        sections=[{"id": "s", "fields": [{"name": "x", "type": "text"}]}],
        template="dummy.j2",
        stage_table={},
    )


# ===================================================================
# 1. derive_stage()
# ===================================================================
class TestDeriveStage:
    def test_exact_match(self, mini_cfg: OrganConfig):
        assert derive_stage(mini_cfg, "T1a", "N0", "M0") == "Stage IA1"

    def test_exact_match_t1b(self, mini_cfg: OrganConfig):
        assert derive_stage(mini_cfg, "T1b", "N0", "M0") == "Stage IA2"

    def test_wildcard_m1a(self, mini_cfg: OrganConfig):
        assert derive_stage(mini_cfg, "T2a", "N0", "M1a") == "Stage IVA"

    def test_wildcard_m1c1(self, mini_cfg: OrganConfig):
        assert derive_stage(mini_cfg, "T1a", "N0", "M1c1") == "Stage IVB"

    def test_p_prefix_stripping(self, mini_cfg: OrganConfig):
        assert derive_stage(mini_cfg, "pT1a", "pN0", "pM0") == "Stage IA1"

    def test_no_match(self, mini_cfg: OrganConfig):
        assert derive_stage(mini_cfg, "TX", "NX", "M0") == "Stage ?"

    # Integration-style with real lung config
    def test_lung_stage_0(self, lung_cfg: OrganConfig):
        assert derive_stage(lung_cfg, "Tis", "N0", "M0") == "Stage 0"

    def test_lung_stage_ib(self, lung_cfg: OrganConfig):
        assert derive_stage(lung_cfg, "T2a", "N0", "M0") == "Stage IB"

    def test_lung_stage_iiia(self, lung_cfg: OrganConfig):
        assert derive_stage(lung_cfg, "T4", "N0", "M0") == "Stage IIIA"

    def test_lung_stage_iiic(self, lung_cfg: OrganConfig):
        assert derive_stage(lung_cfg, "T4", "N3", "M0") == "Stage IIIC"

    def test_lung_stage_iva_m1b(self, lung_cfg: OrganConfig):
        assert derive_stage(lung_cfg, "T3", "N2a", "M1b") == "Stage IVA"

    def test_lung_stage_ivb_m1c2(self, lung_cfg: OrganConfig):
        assert derive_stage(lung_cfg, "T1a", "N0", "M1c2") == "Stage IVB"

    def test_lung_p_prefix(self, lung_cfg: OrganConfig):
        assert derive_stage(lung_cfg, "pT1a", "pN0", "pM0") == "Stage IA1"


# ===================================================================
# 2. build_histologic_summary()
# ===================================================================
class TestBuildHistologicSummary:
    def test_single_ad_with_subtype_and_pct(self, mix_cfg: OrganConfig):
        form = {
            "histologic_type_1": "AD",
            "histologic_subtype_1": "AD_lepidic",
            "histologic_percent_1": "60",
        }
        result = build_histologic_summary(form, mix_cfg)
        assert result == "Invasive non-mucinous adenocarcinoma, lepidic (60%)"

    def test_multiple_ad_subtypes(self, mix_cfg: OrganConfig):
        form = {
            "histologic_type_1": "AD",
            "histologic_subtype_1": "AD_lepidic",
            "histologic_percent_1": "60",
            "histologic_type_2": "AD",
            "histologic_subtype_2": "AD_acinar",
            "histologic_percent_2": "30",
            "histologic_type_3": "AD",
            "histologic_subtype_3": "AD_solid",
            "histologic_percent_3": "10",
        }
        result = build_histologic_summary(form, mix_cfg)
        # primary = lepidic 60%
        assert result.startswith("Invasive non-mucinous adenocarcinoma, lepidic (60%)")
        assert "conventional acinar (30%)" in result
        assert "solid (10%)" in result

    def test_non_ad_single(self, mix_cfg: OrganConfig):
        form = {
            "histologic_type_1": "SQ",
            "histologic_subtype_1": "SQ_keratin",
            "histologic_percent_1": "100",
        }
        result = build_histologic_summary(form, mix_cfg)
        assert "Squamous cell carcinoma, keratinizing type" in result

    def test_mixed_ad_and_sq(self, mix_cfg: OrganConfig):
        form = {
            "histologic_type_1": "AD",
            "histologic_subtype_1": "AD_lepidic",
            "histologic_percent_1": "70",
            "histologic_type_2": "SQ",
            "histologic_subtype_2": "SQ_keratin",
            "histologic_percent_2": "30",
        }
        result = build_histologic_summary(form, mix_cfg)
        assert "Invasive non-mucinous adenocarcinoma" in result
        assert "lepidic (70%)" in result
        assert "Squamous cell carcinoma: Squamous cell carcinoma, keratinizing type (30%)" in result

    def test_empty_form(self, mix_cfg: OrganConfig):
        assert build_histologic_summary({}, mix_cfg) == ""

    def test_no_mix_field(self, no_mix_cfg: OrganConfig):
        form = {"histologic_type_1": "AD", "histologic_percent_1": "100"}
        assert build_histologic_summary(form, no_mix_cfg) == ""


# ===================================================================
# 3. build_nodal_summary()
# ===================================================================
class TestBuildNodalSummary:
    def test_single_station(self):
        form = {"LN1R_positive": "2", "LN1R_total": "5"}
        assert build_nodal_summary(form) == "1R (2/5)"

    def test_multiple_stations(self):
        form = {
            "LN1R_positive": "2",
            "LN1R_total": "5",
            "LN7_positive": "1",
            "LN7_total": "3",
        }
        result = build_nodal_summary(form)
        assert "1R (2/5)" in result
        assert "7 (1/3)" in result

    def test_missing_total(self):
        form = {"LN1R_positive": "2"}
        assert build_nodal_summary(form) == "1R (2/?)"

    def test_empty_form(self):
        assert build_nodal_summary({}) == ""

    def test_skips_zero_positive(self):
        form = {"LN1R_positive": "", "LN1R_total": "5"}
        assert build_nodal_summary(form) == ""


# ===================================================================
# 4. extract_fields()
# ===================================================================
class TestExtractFields:
    def test_radio_passthrough(self, mini_cfg: OrganConfig):
        form = {"color": "red", "size": "", "flag": "", "toppings": "", "note": ""}
        data = extract_fields(form, mini_cfg)
        assert data["color"] == "red"

    def test_number_conversion(self, mini_cfg: OrganConfig):
        form = {"color": "", "size": "42", "flag": "", "toppings": "", "note": ""}
        data = extract_fields(form, mini_cfg)
        assert data["size"] == 42.0

    def test_number_empty(self, mini_cfg: OrganConfig):
        form = {"color": "", "size": "", "flag": "", "toppings": "", "note": ""}
        data = extract_fields(form, mini_cfg)
        assert data["size"] is None

    def test_checkbox_bool_on(self, mini_cfg: OrganConfig):
        form = {"color": "", "size": "", "flag": "on", "toppings": "", "note": ""}
        data = extract_fields(form, mini_cfg)
        assert data["flag"] is True

    def test_checkbox_bool_off(self, mini_cfg: OrganConfig):
        form = {"color": "", "size": "", "flag": "", "toppings": "", "note": ""}
        data = extract_fields(form, mini_cfg)
        assert data["flag"] is False

    def test_checkbox_multi(self, mini_cfg: OrganConfig):
        form = {"color": "", "size": "", "flag": "", "toppings": ["A", "C"], "note": ""}
        data = extract_fields(form, mini_cfg)
        assert data["toppings"] == ["A", "C"]


# ===================================================================
# 5. Helpers
# ===================================================================
class TestNormalizeTnmComponent:
    def test_strip_p_prefix(self):
        assert normalize_tnm_component("pT1a") == "T1a"

    def test_no_prefix(self):
        assert normalize_tnm_component("N0") == "N0"

    def test_empty(self):
        assert normalize_tnm_component("") == ""

    def test_none(self):
        assert normalize_tnm_component(None) == ""

    def test_whitespace(self):
        assert normalize_tnm_component("  pN2a  ") == "N2a"


class TestToBool:
    @pytest.mark.parametrize("val", ["on", "true", "1", "yes", "True", "ON", "YES"])
    def test_truthy(self, val):
        assert to_bool(val) is True

    @pytest.mark.parametrize("val", ["", None, "off", "false", "0", "no", "random"])
    def test_falsy(self, val):
        assert to_bool(val) is False


class TestToFloatOrNone:
    def test_valid_float(self):
        assert to_float_or_none("3.5") == 3.5

    def test_int_string(self):
        assert to_float_or_none("42") == 42.0

    def test_empty(self):
        assert to_float_or_none("") is None

    def test_none(self):
        assert to_float_or_none(None) is None

    def test_invalid(self):
        assert to_float_or_none("abc") is None

    def test_empty_list(self):
        assert to_float_or_none([]) is None


class TestGetlist:
    def test_dict_with_list(self):
        assert getlist({"k": ["a", "b"]}, "k") == ["a", "b"]

    def test_comma_separated(self):
        assert getlist({"k": "a, b, c"}, "k") == ["a", "b", "c"]

    def test_single_value(self):
        assert getlist({"k": "x"}, "k") == ["x"]

    def test_missing_key(self):
        assert getlist({}, "k") == []

    def test_supports_getlist_protocol(self):
        class FakeForm:
            def __init__(self, data):
                self._data = data
            def getlist(self, key):
                return self._data.get(key, [])
            def __contains__(self, key):
                return key in self._data
            def __iter__(self):
                return iter(self._data)

        form = FakeForm({"k": ["x", "y"]})
        assert getlist(form, "k") == ["x", "y"]

    def test_filters_none_and_empty(self):
        assert getlist({"k": ["a", None, "", "b"]}, "k") == ["a", "b"]


class TestParsePct:
    def test_numeric(self):
        assert parse_pct("60") == 60.0

    def test_empty(self):
        assert parse_pct("") == 0.0

    def test_none(self):
        assert parse_pct(None) == 0.0

    def test_invalid(self):
        assert parse_pct("abc") == 0.0

    def test_float_string(self):
        assert parse_pct("33.3") == pytest.approx(33.3)


class TestPickPrimaryRow:
    def test_highest_pct(self):
        rows = [
            {"type_code": "A", "subtype_code": "s1", "pct": 30},
            {"type_code": "A", "subtype_code": "s2", "pct": 70},
        ]
        assert _pick_primary_row(rows)["pct"] == 70

    def test_tie_broken_by_subtype(self):
        rows = [
            {"type_code": "A", "subtype_code": "", "pct": 50},
            {"type_code": "A", "subtype_code": "s1", "pct": 50},
        ]
        assert _pick_primary_row(rows)["subtype_code"] == "s1"

    def test_single_row(self):
        rows = [{"type_code": "X", "subtype_code": "y", "pct": 100}]
        assert _pick_primary_row(rows)["type_code"] == "X"
