"""
SAID (Self-Addressing Identifier) verification for ACDC credentials.

A SAID is the cryptographic digest of the data block it identifies.
It is computed over the block with the 'd' field set to a placeholder
of equal length, then the resulting digest is placed back into 'd'.
Any modification to the credential data invalidates the SAID.
"""
from keri.core.serdering import SerderACDC


def verify_said(credential: dict) -> bool:
    """Recompute the SAID for a credential and compare against its d field.

    Constructs a SerderACDC from the credential dict, which triggers
    KERIpy's internal round-trip verification: it re-serialises the SAD
    with 'd' zeroed, recomputes the digest, and confirms it matches.

    Args:
        credential: raw ACDC credential as a Python dict (must include 'v' and 'd' fields)

    Returns:
        True if the credential's SAID is valid, False otherwise
    """
    try:
        serder = SerderACDC(sad=credential)
        return serder.said == credential.get("d")
    except Exception:
        return False
