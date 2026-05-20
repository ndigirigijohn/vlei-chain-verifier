"""
Tests for key state lookup (Phase 5).

Uses a temporary in-memory Habery (temp=True) so no LMDB files are
created on disk and tests run offline.
"""
import pytest

from keri.app import habbing

from src.keystate import get_key_state_temp


@pytest.fixture(scope="module")
def hby_and_hab():
    """Open a temp Habery, create one Hab, yield both, then close."""
    with habbing.openHby(name="test_ks", temp=True) as hby:
        hab = hby.makeHab(name="alice")
        yield hby, hab


@pytest.fixture(scope="module")
def alice_aid(hby_and_hab):
    _, hab = hby_and_hab
    return hab.pre


@pytest.fixture(scope="module")
def hby(hby_and_hab):
    hby, _ = hby_and_hab
    return hby


class TestGetKeyStateTemp:
    def test_returns_dict_for_known_aid(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        assert result is not None
        assert isinstance(result, dict)

    def test_aid_field_matches(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        assert result["aid"] == alice_aid

    def test_sequence_number_is_zero_at_inception(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        assert result["sequence_number"] == 0

    def test_current_keys_is_nonempty_list(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        keys = result["current_keys"]
        assert isinstance(keys, list)
        assert len(keys) >= 1

    def test_current_keys_are_strings(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        for k in result["current_keys"]:
            assert isinstance(k, str)
            assert len(k) > 0

    def test_next_key_digests_is_list(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        assert isinstance(result["next_key_digests"], list)

    def test_signing_threshold_present(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        assert "signing_threshold" in result
        assert result["signing_threshold"] is not None

    def test_witnesses_is_list(self, hby, alice_aid):
        result = get_key_state_temp(alice_aid, hby)
        assert isinstance(result["witnesses"], list)

    def test_unknown_aid_returns_none(self, hby):
        result = get_key_state_temp("EUnknownAIDThatDoesNotExistInThisKeystore", hby)
        assert result is None

    def test_empty_string_aid_returns_none(self, hby):
        result = get_key_state_temp("", hby)
        assert result is None


class TestGetKeyStateNoDb:
    def test_nonexistent_keystore_returns_none(self):
        """When the keystore does not exist, return None rather than raising."""
        from src.keystate import get_key_state
        result = get_key_state(
            aid="EUnknownAID",
            db_name="this_keystore_does_not_exist_xyz",
            db_base="/tmp/vlei_test_nonexistent",
        )
        assert result is None
