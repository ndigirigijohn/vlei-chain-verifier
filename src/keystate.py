"""
Key state lookup from a local KERIpy LMDB database.

A key state describes the current cryptographic state of a KERI AID:
which public keys are currently valid for signing, what the pre-rotation
commitment is, and which witnesses back the KEL.

This module reads from an existing local database populated by prior
KERIA/kli activity. It does NOT perform live OOBI resolution — that is
Phase 6 (resolve_oobi).

Production path
---------------
To have key state available for an AID, you must first resolve its OOBI:

    kli oobi resolve --name <keystore> --oobi <oobi-url>

or via KERIA's REST API:

    POST /identifiers/{alias}/oobis  {"url": "<oobi-url>"}

After resolution the AID's KEL is stored in the local LMDB keystore and
get_key_state() can return its current state without any network call.
"""
from __future__ import annotations

import pathlib

from keri.app import habbing


def get_key_state(aid: str, db_name: str = "verifier", db_base: str = "") -> dict | None:
    """Retrieve the current key state for an AID from a local KERIpy keystore.

    Opens the LMDB keystore at the path KERIpy derives from (db_base, db_name)
    and looks up the AID in the in-memory Kever cache backed by the database.

    Args:
        aid:     the AID whose key state to retrieve (qb64 prefix string)
        db_name: KERIpy keystore name, maps to ~/.keri/<db_name>/ by default
        db_base: base directory override (empty string = use KERIpy default)

    Returns:
        dict with key state fields if the AID is known, None otherwise:
            aid             — the AID prefix
            sequence_number — integer sequence number of the latest KEL event
            current_keys    — list of current signing public keys (qb64 strings)
            next_key_digests— list of pre-rotation key digests (qb64 strings)
            signing_threshold — signing threshold (string, e.g. '1' or '2/3')
            witnesses       — list of witness AIDs (qb64 strings)

    Notes:
        Returns None (not an exception) when:
        - The AID has never been resolved into this keystore
        - The keystore does not exist yet
        - The database is empty
        This lets callers decide how to handle missing state (warn, skip, error).
    """
    kwargs = dict(name=db_name, temp=False)
    if db_base:
        kwargs["base"] = db_base

    try:
        with habbing.openHby(**kwargs) as hby:
            kever = hby.kevers.get(aid)
            if kever is None:
                return None
            return {
                "aid": aid,
                "sequence_number": kever.sn,
                "current_keys": [v.qb64 for v in kever.verfers],
                "next_key_digests": kever.ndigs,
                "signing_threshold": kever.tholder.sith,
                "witnesses": list(kever.wits),
            }
    except Exception:
        return None


def get_key_state_temp(aid: str, hby: habbing.Habery) -> dict | None:
    """Look up key state from an already-open Habery instance.

    Used in tests and in the OOBI resolver (Phase 6) where the Habery
    is opened by the caller rather than by this function.

    Args:
        aid: AID prefix to look up
        hby: open Habery whose kevers dict will be queried

    Returns:
        same structure as get_key_state(), or None if AID not found
    """
    kever = hby.kevers.get(aid)
    if kever is None:
        return None
    return {
        "aid": aid,
        "sequence_number": kever.sn,
        "current_keys": [v.qb64 for v in kever.verfers],
        "next_key_digests": kever.ndigs,
        "signing_threshold": kever.tholder.sith,
        "witnesses": list(kever.wits),
    }
