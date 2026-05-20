"""
Schema SAID verification against the GLEIF schema registry.

Each ACDC credential references a schema by its SAID (the 's' field).
This module fetches the schema document from the GLEIF registry and
confirms that its content hashes to the expected SAID.

Network is only used in fetch_and_verify_schema(). All other functions
are pure and work offline.
"""
import requests

from keri.core.coring import Saider, Saids, MtrDex

# GLEIF testnet schema server — verify this URL against official docs before use:
# https://www.gleif.org/newsroom/events/gleif-vlei-hackathon-2025/
GLEIF_SCHEMA_SERVER = "https://schema.vlei.dev/oobi"

# Known vLEI schema SAIDs → human-readable credential type names.
# These are testnet values — version-specific, verify before use in production.
SCHEMA_TYPES: dict[str, str] = {
    "EBfdlu8R27Fbx-ehrqwImnyjnB2YpMgOEOs9OkdeKFzw": "QVI",
    "ENPXp1vQzRF6ELV5kl2uraw4MrmsTXgng1xdt4n2pHfn": "LE",
    "EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy": "OOR",
    "EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw": "ECR",
}


def resolve_credential_type(schema_said: str) -> str:
    """Map a schema SAID to a human-readable vLEI credential type name.

    Args:
        schema_said: the 's' field from an ACDC credential

    Returns:
        credential type label e.g. 'QVI', 'LE', 'OOR', 'ECR', or 'Unknown'
    """
    return SCHEMA_TYPES.get(schema_said, "Unknown")


def verify_schema_said(schema: dict, expected_said: str) -> bool:
    """Verify that a schema document's content matches its claimed SAID.

    Recomputes the SAID over the schema dict (with '$id' zeroed) and
    compares to the expected value. This is the same algorithm as
    credential SAID verification but using '$id' as the label instead of 'd'.

    Args:
        schema: schema document as a Python dict (must contain '$id')
        expected_said: the SAID we expect the schema to have

    Returns:
        True if the schema content matches expected_said, False otherwise
    """
    try:
        saider = Saider(qb64=expected_said, label=Saids.dollar)
        return saider.verify(schema, prefixed=True, label=Saids.dollar)
    except Exception:
        return False


def fetch_and_verify_schema(schema_said: str, timeout: int = 10) -> bool:
    """Fetch a schema from the GLEIF registry and verify its SAID.

    Makes a GET request to the GLEIF schema server, parses the response
    as JSON, then recomputes the SAID to confirm the document has not
    been tampered with since it was published.

    Args:
        schema_said: the SAID of the schema to fetch and verify
        timeout: HTTP request timeout in seconds

    Returns:
        True if the schema was fetched and its SAID is valid
        False if the request failed, the response is not valid JSON,
              or the SAID does not match the document content
    """
    url = f"{GLEIF_SCHEMA_SERVER}/{schema_said}"
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException:
        return False

    if response.status_code != 200:
        return False

    try:
        schema = response.json()
    except ValueError:
        return False

    return verify_schema_said(schema, schema_said)
