#!/usr/bin/env python3
"""
vLEI Credential Chain Verifier — CLI entry point.

Usage:
    # Verify a single credential (SAID + parsed fields)
    python verifier.py credential.json

    # Verify the full trust chain from a chain manifest
    python verifier.py credential.json --chain fixtures/chain.json

    # Also verify the credential schema against the GLEIF registry (requires network)
    python verifier.py credential.json --chain fixtures/chain.json --verify-schema
"""
import argparse
import json
import pathlib
import sys

from src.acdc import parse_credential, extract_edge_saids
from src.chain import display_chain, GLEIF_ROOT_AIDS
from src.said import verify_said
from src.schema import fetch_and_verify_schema, resolve_credential_type

SEPARATOR = "─" * 56


def load_json(path: str) -> dict:
    try:
        return json.loads(pathlib.Path(path).read_text())
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def print_header(cred_raw: dict, verify_schema: bool) -> None:
    """Print the credential header block (type, SAID, schema line)."""
    cred = parse_credential(cred_raw)
    cred_type = resolve_credential_type(cred.schema_said)
    said_ok = verify_said(cred_raw)

    print(f"\nCredential:    {cred_type}")
    print(f"SAID:          {cred.said}")

    schema_status = ""
    if verify_schema:
        schema_ok = fetch_and_verify_schema(cred.schema_said)
        schema_status = "  ✓ valid" if schema_ok else "  ✗ INVALID"

    print(f"Schema:        {cred.schema_said}{schema_status}")
    print(f"SAID verified: {'✓' if said_ok else '✗ INVALID'}")


def run_single(cred_raw: dict, verify_schema: bool) -> None:
    """Inspect a single credential without chain traversal."""
    cred = parse_credential(cred_raw)

    print(f"Credential SAID : {cred.said}")
    print(f"Issuer AID      : {cred.issuer}")
    print(f"Schema SAID     : {cred.schema_said}  ({resolve_credential_type(cred.schema_said)})")
    print(f"Registry SAID   : {cred.registry}")
    print(f"SAID verified   : {'✓' if verify_said(cred_raw) else '✗ INVALID'}")

    if verify_schema:
        ok = fetch_and_verify_schema(cred.schema_said)
        print(f"Schema verified : {'✓' if ok else '✗ INVALID'}")

    edge_saids = extract_edge_saids(cred)
    if edge_saids:
        print(f"Edge SAIDs      :")
        for s in edge_saids:
            print(f"  → {s}")
    else:
        print(f"Edge SAIDs      : (none — root credential)")

    attrs = {k: v for k, v in cred.attributes.items() if k != "d"}
    if attrs:
        print(f"Attributes      :")
        for k, v in attrs.items():
            print(f"  {k}: {v}")


def run_chain(first_cred_raw: dict, chain_path: str, verify_schema: bool) -> None:
    """Load and display the full trust chain from a chain manifest file."""
    chain_data = load_json(chain_path)
    chain_files = chain_data.get("files", [])
    gleif_root = chain_data.get("gleif_root")

    if not chain_files:
        print("Error: chain.json has no 'files' list.", file=sys.stderr)
        sys.exit(1)

    # Load all credentials from the file list (paths relative to project root)
    project_root = pathlib.Path(__file__).parent
    credentials = []
    for fpath in chain_files:
        raw = load_json(str(project_root / fpath))
        credentials.append(parse_credential(raw))

    # Build the active GLEIF root set — merge the hardcoded set with any
    # fixture-specific root captured at generation time
    root_aids = set(GLEIF_ROOT_AIDS)
    if gleif_root:
        root_aids.add(gleif_root)

    # Print the header using the first credential in the chain
    first = credentials[0] if credentials else parse_credential(first_cred_raw)
    cred_type = resolve_credential_type(first.schema_said)
    said_ok = verify_said(first.raw)

    print(f"\nCredential:    {cred_type}")
    print(f"SAID:          {first.said}")

    schema_status = ""
    if verify_schema:
        schema_ok = fetch_and_verify_schema(first.schema_said)
        schema_status = "  ✓ valid" if schema_ok else "  ✗ INVALID"
    print(f"Schema:        {first.schema_said}{schema_status}")

    display_chain(credentials, root_aids)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="vLEI Credential Chain Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("credential", help="path to the ACDC credential JSON file")
    parser.add_argument(
        "--chain",
        metavar="FILE",
        help="path to chain.json manifest (enables full chain traversal)",
    )
    parser.add_argument(
        "--verify-schema",
        action="store_true",
        help="fetch and verify the schema from the GLEIF schema server (requires network)",
    )
    args = parser.parse_args()

    print("\nvLEI Credential Chain Verifier")
    print(SEPARATOR)

    cred_raw = load_json(args.credential)

    if args.chain:
        run_chain(cred_raw, args.chain, args.verify_schema)
    else:
        run_single(cred_raw, args.verify_schema)


if __name__ == "__main__":
    main()
