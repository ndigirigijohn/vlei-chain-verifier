# vLEI Credential Chain Verifier

A Python CLI tool that verifies a vLEI ACDC credential against the full trust chain — SAID integrity, schema validation, and edge traversal from the credential up to the GLEIF root AID.

## Quick Start

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
# Verify a single credential
python verifier.py credentials/my_ecr.json

# Verify the full trust chain
python verifier.py credentials/my_ecr.json --chain chain.json

# Also verify the schema against the GLEIF registry (requires network)
python verifier.py credentials/my_ecr.json --chain chain.json --verify-schema
```

## Sample Output

```
vLEI Credential Chain Verifier
────────────────────────────────────────────────────────

Credential:    ECR
SAID:          EKVR6fidbnBbw9je6pPbdIrXSEDHwX-CXYVwu_uU6upg
Schema:        EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw

Chain:
  [1] ECR Credential  ← you
       Issued by: EA4C5U10VgXCCvQtnioj-Nuc7Ey5dNQwHVMNWDhPj6...
       SAID verified ✓
  [2] LE Credential
       Issued by: EDu1j3r9_2F9aIEVHaMvQ5u6Sr5ig023KXVScRPrQy...
       SAID verified ✓
  [3] QVI Credential
       Issued by: EGzi85A91B597MOBqgBoJTkyvWHhRSO-UWooYKEosk...
       SAID verified ✓

  [GLEIF Root AID]
       Known root — trust anchor ✓

Result: VALID — full chain verified to GLEIF root ✓
```

## Documentation

- [Architecture](docs/architecture.md) — trust chain model, module overview, data flow
- [Usage](docs/usage.md) — CLI reference, credential format, testing with fixtures
- [Credential Format](docs/credential-format.md) — vLEI field reference, schema SAIDs, chain structure

## Run Tests

```bash
pytest tests/
```

## Requirements

- Python 3.14+
- `hio` and `keripy` are installed from GitHub (pre-release, not yet on PyPI)
- See `requirements.txt`
