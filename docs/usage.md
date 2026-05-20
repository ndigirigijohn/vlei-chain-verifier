# Usage

## Install

Requires Python 3.14+. Both `hio` and `keripy` are pre-release and not yet on PyPI.

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## CLI Reference

```
python verifier.py <credential.json> [options]
```

| Option | Description |
|---|---|
| `<credential.json>` | Path to the ACDC credential file to verify |
| `--chain FILE` | Path to a `chain.json` manifest for full trust chain traversal |
| `--verify-schema` | Fetch and verify the credential's schema from the GLEIF registry (requires network) |
| `--oobi URL` | Resolve an OOBI URL to fetch an issuer's key state (requires live endpoint, repeatable) |

---

## Testing with the Included Fixtures

The `fixtures/` directory contains a complete synthetic three-level vLEI chain with valid, self-consistent SAIDs. No network is needed.

```bash
# Inspect a single credential
python verifier.py fixtures/sample_ecr.json
```

```
vLEI Credential Chain Verifier
────────────────────────────────────────────────────────
Credential SAID : EKVR6fidbnBbw9je6pPbdIrXSEDHwX-CXYVwu_uU6upg
Issuer AID      : EA4C5U10VgXCCvQtnioj-Nuc7Ey5dNQwHVMNWDhPj6hw
Schema SAID     : EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw  (ECR)
Registry SAID   : EBfMDFWxNHYCQ4jbTnmFMwc2N2gHbA6N8LF1LFkpGMek
SAID verified   : ✓
Edge SAIDs      :
  → EI_Kdmh0BOMVdaj95sRoxTubRwx9b3gx2kP1NC4MdRgi
Attributes      :
  personLegalName: Jane Smith
  engagementContextRole: Chief Financial Officer
  LEI: 254900OPPU84GM83MG36
```

```bash
# Full chain traversal
python verifier.py fixtures/sample_ecr.json --chain fixtures/chain.json
```

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

---

## Using a Real Credential

### Credential file format

The credential must be a JSON file containing a valid ACDC. Minimum required fields:

```json
{
  "v": "ACDC10JSON...",
  "d": "<credential SAID>",
  "i": "<issuer AID>",
  "s": "<schema SAID>",
  "a": { ... },
  "e": { ... }
}
```

See [Credential Format](credential-format.md) for a full field reference.

### Chain manifest format

`chain.json` lists the credential files in order from leaf to root, and names the GLEIF root AID:

```json
{
  "files": [
    "path/to/ecr.json",
    "path/to/le.json",
    "path/to/qvi.json"
  ],
  "gleif_root": "<GLEIF root AID>"
}
```

File paths are relative to the project root.

### Schema verification (network)

```bash
python verifier.py ecr.json --verify-schema
```

Fetches `https://schema.vlei.dev/oobi/<schema_said>` and recomputes the schema SAID to confirm it matches. Requires connectivity to the GLEIF testnet schema server.

### OOBI resolution (live endpoint)

```bash
python verifier.py ecr.json \
    --oobi "http://<witness>/oobi/<LE_AID>/witness/<WitnessAID>" \
    --oobi "http://<witness>/oobi/<QVI_AID>/witness/<WitnessAID>"
```

Resolves each issuer AID's Key Event Log from a live KERIA agent or witness. The `--oobi` flag can be repeated for multiple issuers in the chain. If the endpoint is unreachable the verifier prints a warning and continues with SAID-only verification.

---

## Regenerating the Test Fixtures

The fixtures in `fixtures/` are pre-generated synthetic credentials. To regenerate them (e.g. after modifying `make_fixtures.py`):

```bash
python scripts/make_fixtures.py
```

This creates new `sample_ecr.json`, `sample_le.json`, `sample_qvi.json`, and `chain.json` with fresh AIDs and SAIDs. All tests will continue to pass because they read the fixture files at runtime.

> **Note:** Each run of `make_fixtures.py` generates new random AIDs. The SAIDs in the fixture files will change. If you have hardcoded any SAIDs in your own code, update them after regenerating.

---

## Running Tests

```bash
pytest tests/
```

```bash
# With coverage
pytest tests/ --tb=short -q
```

Tests run fully offline. Schema verification tests mock `requests.get`. OOBI resolution is not unit-tested (requires a live endpoint).

---

## Adding the GLEIF Root AID

The hardcoded `GLEIF_ROOT_AIDS` set in `src/chain.py` contains a placeholder. To verify against a real credential chain, add the actual GLEIF testnet root AID:

```python
# src/chain.py
GLEIF_ROOT_AIDS: set[str] = {
    "EDP1vHcw_wc4M__Fj53-cJaBnZZASd-aN0-oZe4kHsSi",  # verify against GLEIF docs
}
```

The current GLEIF root AID can be confirmed from the GLEIF testnet documentation or by inspecting a known-good QVI credential's `i` field.
