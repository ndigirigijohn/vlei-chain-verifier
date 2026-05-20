"""
Key state lookup and OOBI resolution using KERIpy.

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

from keri.app import habbing, oobiing
from keri.app.directing import runController
from keri.app.oobiing import Result
from keri.help import helping
from keri.recording import OobiRecord


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


def resolve_oobi(oobi_url: str, expire: float = 10.0) -> dict | None:
    """Resolve an OOBI URL and return the AID's current key state.

    An OOBI (Out-of-Band Introduction) URL pairs an AID with a network
    location where its Key Event Log can be fetched and verified:

        http://<witness-host>/oobi/<AID>/witness/<witness-AID>

    This function:
    1. Opens a temporary in-memory Habery (no files written to disk)
    2. Queues the OOBI URL for resolution
    3. Runs KERIpy's hio event loop for up to `expire` seconds
    4. If the AID's KEL was fetched and verified, returns the key state
    5. Returns None on any failure: unreachable endpoint, timeout, invalid KEL

    Args:
        oobi_url: OOBI URL string, e.g.
                  "http://witnesshost/oobi/<AID>/witness/<WitnessAID>"
        expire:   maximum seconds to wait for resolution (default 10.0)

    Returns:
        dict with key state fields (same structure as get_key_state_temp),
        or None if resolution failed or timed out

    Requires:
        A reachable KERIA agent or witness endpoint at the URL.
        Returns None (not an exception) when the endpoint is unreachable.

    Notes on KERIpy's event loop:
        KERIpy uses hio (synchronous coroutines), not asyncio. There is no
        async/await. Resolution runs as a doer inside runController's Doist
        event loop. The loop exits after `expire` seconds whether or not
        resolution succeeded — check hby.kevers to see what was resolved.
    """
    try:
        with habbing.openHby(name="oobi_resolver", temp=True) as hby:
            oobiery = oobiing.Oobiery(hby=hby)

            # Queue the OOBI URL for resolution
            obr = OobiRecord(date=helping.nowIso8601())
            hby.db.oobis.pin(keys=(oobi_url,), val=obr)

            # Run the hio event loop — blocks for up to `expire` seconds
            runController(doers=oobiery.doers, expire=expire)

            # Check whether resolution succeeded
            result = hby.db.roobi.get(keys=(oobi_url,))
            if result is None or result.state != Result.resolved:
                return None

            # Return the key state of the first (and typically only) resolved AID
            for pre, kever in hby.kevers.items():
                return {
                    "aid": pre,
                    "sequence_number": kever.sn,
                    "current_keys": [v.qb64 for v in kever.verfers],
                    "next_key_digests": kever.ndigs,
                    "signing_threshold": kever.tholder.sith,
                    "witnesses": list(kever.wits),
                }
    except Exception:
        pass

    return None
