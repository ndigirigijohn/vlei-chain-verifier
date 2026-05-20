"""
Tests for ACDC credential parsing (Phase 2).
"""
import json
import pathlib

import pytest

from src.acdc import ACDCCredential, parse_credential, extract_edge_saids

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def ecr_raw() -> dict:
    return json.loads((FIXTURES / "sample_ecr.json").read_text())


@pytest.fixture
def le_raw() -> dict:
    return json.loads((FIXTURES / "sample_le.json").read_text())


@pytest.fixture
def qvi_raw() -> dict:
    return json.loads((FIXTURES / "sample_qvi.json").read_text())


@pytest.fixture
def ecr(ecr_raw) -> ACDCCredential:
    return parse_credential(ecr_raw)


@pytest.fixture
def le(le_raw) -> ACDCCredential:
    return parse_credential(le_raw)


@pytest.fixture
def qvi(qvi_raw) -> ACDCCredential:
    return parse_credential(qvi_raw)


class TestParseCredential:
    def test_returns_acdc_credential(self, ecr):
        assert isinstance(ecr, ACDCCredential)

    def test_said_field(self, ecr, ecr_raw):
        assert ecr.said == ecr_raw["d"]

    def test_issuer_field(self, ecr, ecr_raw):
        assert ecr.issuer == ecr_raw["i"]

    def test_schema_said_field(self, ecr, ecr_raw):
        assert ecr.schema_said == ecr_raw["s"]

    def test_registry_field(self, ecr, ecr_raw):
        assert ecr.registry == ecr_raw["ri"]

    def test_attributes_field(self, ecr, ecr_raw):
        assert ecr.attributes == ecr_raw["a"]

    def test_edges_field(self, ecr, ecr_raw):
        assert ecr.edges == ecr_raw["e"]

    def test_raw_preserved(self, ecr, ecr_raw):
        assert ecr.raw == ecr_raw

    def test_optional_edges_defaults_to_empty(self):
        """Credentials without an edges block should not raise."""
        raw = {
            "d": "EBfdlu8R27Fbx-ehrqwImnyjnB2YpMgOEOs9OkdeKFzw",
            "i": "EDYbGv_s3XIJ8aJbjCPhaSFL0RPtAasH8YAn1N2uSE0H",
            "s": "EBfdlu8R27Fbx-ehrqwImnyjnB2YpMgOEOs9OkdeKFzw",
            "a": {},
        }
        cred = parse_credential(raw)
        assert cred.edges == {}
        assert cred.rules == {}
        assert cred.registry == ""

    def test_missing_required_field_raises(self):
        with pytest.raises(KeyError):
            parse_credential({"d": "abc"})  # missing 'i' and 's'


class TestExtractEdgeSaids:
    def test_ecr_has_one_edge_to_le(self, ecr, le_raw):
        saids = extract_edge_saids(ecr)
        assert len(saids) == 1
        assert saids[0] == le_raw["d"]

    def test_le_has_one_edge_to_qvi(self, le, qvi_raw):
        saids = extract_edge_saids(le)
        assert len(saids) == 1
        assert saids[0] == qvi_raw["d"]

    def test_qvi_has_no_edges(self, qvi):
        saids = extract_edge_saids(qvi)
        assert saids == []

    def test_d_key_is_skipped(self, ecr):
        """The 'd' key of the edge block (its own SAID) must not be returned."""
        saids = extract_edge_saids(ecr)
        for s in saids:
            assert s != ecr.edges.get("d")

    def test_empty_edges_returns_empty_list(self):
        raw = {"d": "x", "i": "y", "s": "z", "a": {}}
        cred = parse_credential(raw)
        assert extract_edge_saids(cred) == []
