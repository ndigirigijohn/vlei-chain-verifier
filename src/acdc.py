"""
ACDC credential structure parser.

Parses a raw ACDC credential dict into a typed dataclass and extracts
edge SAIDs for chain traversal. No network or key state required.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ACDCCredential:
    """Typed representation of a parsed ACDC credential.

    Fields map directly to the ACDC SAD (Self-Addressing Data) structure:
        v   — version string (protocol/kind/size)
        d   — SAID of this credential (the self-addressing identifier)
        i   — issuer AID
        s   — schema SAID
        ri  — registry SAID (Transaction Event Log identifier)
        a   — attributes block (contains the subject/claims)
        e   — edges block (links to parent credentials in the chain)
        r   — rules block (legal or policy text, optional)
        raw — original dict, kept for SAID re-verification
    """
    said: str
    issuer: str
    schema_said: str
    registry: str
    attributes: dict
    edges: dict
    rules: dict
    raw: dict = field(repr=False)


def parse_credential(raw: dict) -> ACDCCredential:
    """Parse a raw ACDC credential dict into an ACDCCredential.

    Args:
        raw: credential dict loaded from JSON

    Returns:
        ACDCCredential with all fields populated

    Raises:
        KeyError: if required fields 'd', 'i', or 's' are missing
    """
    return ACDCCredential(
        said=raw["d"],
        issuer=raw["i"],
        schema_said=raw["s"],
        registry=raw.get("ri", ""),
        attributes=raw.get("a", {}),
        edges=raw.get("e", {}),
        rules=raw.get("r", {}),
        raw=raw,
    )


def extract_edge_saids(credential: ACDCCredential) -> list[str]:
    """Extract the SAIDs of credentials this one chains to.

    The edges block ('e') has the structure:
        {
          "d": "<SAID of the edge block itself>",
          "<edge_name>": {
              "n": "<SAID of the referenced credential>",
              "s": "<schema SAID of the referenced credential>"
          },
          ...
        }

    We skip the 'd' key (the block's own SAID) and collect the 'n'
    (node) SAID from each named edge.

    Args:
        credential: parsed ACDCCredential

    Returns:
        list of SAIDs of credentials referenced by this credential's edges
    """
    saids = []
    for key, value in credential.edges.items():
        if key == "d":
            continue
        if isinstance(value, dict) and "n" in value:
            saids.append(value["n"])
    return saids
