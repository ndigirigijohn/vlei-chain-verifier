#!/usr/bin/env python3
"""
vLEI Credential Chain Verifier — CLI entry point.

Usage:
    python verifier.py credential.json
    python verifier.py credential.json --chain fixtures/chain.json
"""
import argparse
import json
import pathlib
import sys

from src.acdc import parse_credential, extract_edge_saids
from src.said import verify_said


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


def print_credential_summary(cred_raw: dict) -> None:
    """Print a single credential's parsed fields and SAID status."""
    cred = parse_credential(cred_raw)
    said_ok = verify_said(cred_raw)

    print(f"Credential SAID : {cred.said}")
    print(f"Issuer AID      : {cred.issuer}")
    print(f"Schema SAID     : {cred.schema_said}")
    print(f"Registry SAID   : {cred.registry}")
    print(f"SAID verified   : {'✓' if said_ok else '✗ INVALID'}")

    edge_saids = extract_edge_saids(cred)
    if edge_saids:
        print(f"Edge SAIDs      :")
        for s in edge_saids:
            print(f"  → {s}")
    else:
        print(f"Edge SAIDs      : (none — this is a root credential)")

    attrs = {k: v for k, v in cred.attributes.items() if k != "d"}
    if attrs:
        print(f"Attributes      :")
        for k, v in attrs.items():
            print(f"  {k}: {v}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="vLEI Credential Chain Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("credential", help="path to the ACDC credential JSON file")
    parser.add_argument(
        "--chain",
        metavar="FILE",
        help="path to chain.json listing credential SAIDs in order (not yet used for resolution)",
    )
    args = parser.parse_args()

    print("\nvLEI Credential Chain Verifier")
    print(SEPARATOR)

    cred_raw = load_json(args.credential)
    print_credential_summary(cred_raw)

    if args.chain:
        chain_data = load_json(args.chain)
        saids = chain_data.get("chain", [])
        print(f"\nChain order ({len(saids)} credentials):")
        for i, s in enumerate(saids, 1):
            print(f"  [{i}] {s}")


if __name__ == "__main__":
    main()
