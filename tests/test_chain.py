"""
Tests for edge chain traversal and display (Phase 4).
"""
import copy
import io
import json
import pathlib

import pytest

from src.acdc import parse_credential, ACDCCredential
from src.chain import ChainEntry, verify_chain, display_chain, GLEIF_ROOT_AIDS

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"

# The fixture GLEIF root AID is generated at fixture-creation time and
# stored in chain.json so tests stay consistent across runs.
_chain_meta = json.loads((FIXTURES / "chain.json").read_text())
FIXTURE_GLEIF_ROOT = _chain_meta["gleif_root"]
FIXTURE_ROOT_AIDS = {FIXTURE_GLEIF_ROOT}


@pytest.fixture
def qvi() -> ACDCCredential:
    return parse_credential(json.loads((FIXTURES / "sample_qvi.json").read_text()))


@pytest.fixture
def le() -> ACDCCredential:
    return parse_credential(json.loads((FIXTURES / "sample_le.json").read_text()))


@pytest.fixture
def ecr() -> ACDCCredential:
    return parse_credential(json.loads((FIXTURES / "sample_ecr.json").read_text()))


@pytest.fixture
def full_chain(ecr, le, qvi) -> list[ACDCCredential]:
    return [ecr, le, qvi]


class TestVerifyChain:
    def test_returns_one_entry_per_credential(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert len(entries) == 3

    def test_entries_are_chain_entry_instances(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        for e in entries:
            assert isinstance(e, ChainEntry)

    def test_said_valid_for_all_unmodified(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        for e in entries:
            assert e.said_valid is True

    def test_index_starts_at_one(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert entries[0].index == 1
        assert entries[2].index == 3

    def test_ecr_label(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert entries[0].label == "ECR"

    def test_le_label(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert entries[1].label == "LE"

    def test_qvi_label(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert entries[2].label == "QVI"

    def test_qvi_is_root_issuer(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert entries[2].is_root_issuer is True

    def test_ecr_and_le_are_not_root_issuers(self, full_chain):
        entries = verify_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert entries[0].is_root_issuer is False
        assert entries[1].is_root_issuer is False

    def test_tampered_credential_fails_said(self, full_chain):
        bad_raw = copy.deepcopy(full_chain[0].raw)
        bad_raw["a"]["personLegalName"] = "Tampered"
        bad_cred = parse_credential(bad_raw)
        chain = [bad_cred, full_chain[1], full_chain[2]]
        entries = verify_chain(chain, FIXTURE_ROOT_AIDS)
        assert entries[0].said_valid is False
        # other entries still valid
        assert entries[1].said_valid is True
        assert entries[2].said_valid is True

    def test_unknown_root_aid_not_detected(self, full_chain):
        entries = verify_chain(full_chain, {"EUNKNOWN_AID_PLACEHOLDER"})
        for e in entries:
            assert e.is_root_issuer is False


class TestDisplayChain:
    def test_valid_chain_returns_true(self, full_chain, capsys):
        result = display_chain(full_chain, FIXTURE_ROOT_AIDS)
        assert result is True

    def test_output_contains_each_credential_type(self, full_chain, capsys):
        display_chain(full_chain, FIXTURE_ROOT_AIDS)
        out = capsys.readouterr().out
        assert "ECR Credential" in out
        assert "LE Credential" in out
        assert "QVI Credential" in out

    def test_output_contains_gleif_root_anchor(self, full_chain, capsys):
        display_chain(full_chain, FIXTURE_ROOT_AIDS)
        out = capsys.readouterr().out
        assert "GLEIF Root AID" in out
        assert "trust anchor" in out

    def test_output_contains_result_valid(self, full_chain, capsys):
        display_chain(full_chain, FIXTURE_ROOT_AIDS)
        out = capsys.readouterr().out
        assert "VALID" in out

    def test_tampered_chain_returns_false(self, full_chain, capsys):
        bad_raw = copy.deepcopy(full_chain[0].raw)
        bad_raw["a"]["personLegalName"] = "Tampered"
        bad_cred = parse_credential(bad_raw)
        chain = [bad_cred, full_chain[1], full_chain[2]]
        result = display_chain(chain, FIXTURE_ROOT_AIDS)
        assert result is False

    def test_unknown_root_returns_partial(self, full_chain, capsys):
        result = display_chain(full_chain, {"EUNKNOWN"})
        assert result is False
        out = capsys.readouterr().out
        assert "PARTIAL" in out

    def test_first_entry_marked_as_you(self, full_chain, capsys):
        display_chain(full_chain, FIXTURE_ROOT_AIDS)
        out = capsys.readouterr().out
        assert "← you" in out
