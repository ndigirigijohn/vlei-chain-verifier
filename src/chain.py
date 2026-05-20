"""
Edge chain traversal and trust chain display.

Walks a list of ACDCCredentials from leaf to root, verifies each
SAID, resolves credential type labels, and detects the GLEIF root
trust anchor. Works entirely from credential files — no network needed.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.acdc import ACDCCredential
from src.said import verify_said
from src.schema import resolve_credential_type

SEPARATOR = "─" * 56

# Known GLEIF root AIDs on the testnet.
# The QVI credential is issued directly by one of these AIDs.
# Verify against GLEIF documentation before use in production.
GLEIF_ROOT_AIDS: set[str] = {
    "EDP1vHcw_wc4M__Fj53-cJaBnZZASd-aN0-oZe4kHsSi",  # testnet placeholder
}


@dataclass
class ChainEntry:
    """Result for one level of the verified trust chain."""
    index: int
    label: str           # human-readable type: 'ECR', 'LE', 'QVI', 'Unknown'
    said: str
    issuer: str
    said_valid: bool
    is_root_issuer: bool  # True when this credential was issued by the GLEIF root AID


def verify_chain(
    credentials: list[ACDCCredential],
    gleif_root_aids: set[str] | None = None,
) -> list[ChainEntry]:
    """Verify each credential in the chain and return structured results.

    Args:
        credentials: ordered list from leaf (ECR) to root (QVI)
        gleif_root_aids: set of known GLEIF root AIDs; defaults to GLEIF_ROOT_AIDS

    Returns:
        list of ChainEntry, one per credential
    """
    roots = gleif_root_aids if gleif_root_aids is not None else GLEIF_ROOT_AIDS
    entries = []
    for i, cred in enumerate(credentials, 1):
        entries.append(ChainEntry(
            index=i,
            label=resolve_credential_type(cred.schema_said),
            said=cred.said,
            issuer=cred.issuer,
            said_valid=verify_said(cred.raw),
            is_root_issuer=(cred.issuer in roots),
        ))
    return entries


def display_chain(
    credentials: list[ACDCCredential],
    gleif_root_aids: set[str] | None = None,
) -> bool:
    """Display the full vLEI trust chain and return whether it is valid.

    Prints one block per credential, then a final GLEIF root anchor line
    when the last credential's issuer is a known root AID.

    Args:
        credentials: ordered list from leaf (ECR) to root (QVI)
        gleif_root_aids: set of known GLEIF root AIDs; defaults to GLEIF_ROOT_AIDS

    Returns:
        True if every SAID is valid and the chain ends at a known GLEIF root
    """
    roots = gleif_root_aids if gleif_root_aids is not None else GLEIF_ROOT_AIDS
    entries = verify_chain(credentials, roots)

    print("\nChain:")
    all_said_valid = True

    for entry in entries:
        issuer_short = entry.issuer[:42] + "..." if len(entry.issuer) > 42 else entry.issuer
        first_marker = "  ← you" if entry.index == 1 else ""

        print(f"  [{entry.index}] {entry.label} Credential{first_marker}")
        print(f"       Issued by: {issuer_short}")
        said_mark = "✓" if entry.said_valid else "✗ INVALID"
        print(f"       SAID verified {said_mark}")

        if not entry.said_valid:
            all_said_valid = False

    # Append the GLEIF root anchor if the last credential's issuer is known
    last = entries[-1] if entries else None
    root_reached = last is not None and last.is_root_issuer

    if root_reached:
        print(f"\n  [GLEIF Root AID]")
        print(f"       Known root — trust anchor ✓")

    print()
    if all_said_valid and root_reached:
        print("Result: VALID — full chain verified to GLEIF root ✓")
        return True
    elif all_said_valid and not root_reached:
        print("Result: PARTIAL — all SAIDs valid but GLEIF root not reached")
        return False
    else:
        print("Result: INVALID — one or more SAIDs failed verification ✗")
        return False
