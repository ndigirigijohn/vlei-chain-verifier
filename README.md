# vLEI Credential Chain Verifier

A Python CLI tool that takes a vLEI ACDC credential and verifies it against the full vLEI trust chain — SAID integrity, issuer signature, and edge traversal from the credential up to the GLEIF root.

Built as a direct analogue to [GLEIF-IT/vlei-verifier](https://github.com/GLEIF-IT/vlei-verifier), using [KERIpy](https://github.com/WebOfTrust/keripy) primitives.

## What It Does

```
$ python verifier.py credential.json

vLEI Credential Chain Verifier
────────────────────────────────────────────────────────

Credential:    ECR — Engagement Context Role
SAID:          EBfdlu8R27Fbx-ehrqwImnyjnB2YpMgOEOs9OkdeKFzw
Schema:        EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy  ✓ valid

Chain:
  [1] ECR Credential        ← you
       Issued by: Legal Entity AID (EQzFVaMasUf4cZZBKA0pUbzpvtElrSalhCc8Xx...)
       SAID verified ✓  |  Signature verified ✓

  [2] LE Credential
       Issued by: QVI AID (EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDly2M6N45n...)
       SAID verified ✓  |  Signature verified ✓

  [3] QVI Credential
       Issued by: GLEIF AID (EDP1vHcw_wc4M__Fj53-cJaBnZZASd-aN0-oZe4...)
       SAID verified ✓  |  Signature verified ✓

  [4] GLEIF Root AID
       Known root — trust anchor ✓

Result: VALID — full chain verified to GLEIF root ✓
```

## Trust Chain

```
ECR credential
  └─ edge → LE credential
               └─ edge → QVI credential
                            └─ edge → GLEIF root AID (trust anchor)
```

Each edge reference is a SAID. Traversal means: resolve each SAID, verify it, follow its edges, repeat until the known GLEIF root is reached.

## Implementation Phases

| Phase | Module | What it does |
|-------|--------|-------------|
| 1 | `src/said.py` | SAID recomputation and verification |
| 2 | `src/acdc.py` | ACDC structure parsing and edge extraction |
| 3 | `src/schema.py` | Schema SAID verification against GLEIF registry |
| 4 | `src/chain.py` | Edge chain traversal and display |
| 5 | `src/keystate.py` | KERIpy key state lookup from local DB |
| 6 | `src/keystate.py` | OOBI-based live KEL resolution (stretch) |

## Install

Requires Python 3.14+. Both `hio` and `keripy` are pre-release and not yet on PyPI, so they are installed directly from GitHub.

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Verify SAID of a single credential
python verifier.py fixtures/sample_ecr.json

# Verify against a manually assembled chain
python verifier.py fixtures/sample_ecr.json --chain fixtures/chain.json
```

## Run Tests

```bash
pytest tests/
```

## Key Concepts

**SAID (Self-Addressing Identifier):** The `d` field of an ACDC is the cryptographic digest of the credential block, computed with `d` set to a placeholder of equal length. Any tampering changes the digest and breaks the SAID.

**Edge traversal:** The `e` block of an ACDC contains `{key: {"n": <SAID>}}` entries linking to parent credentials. The verifier follows these until it reaches a known GLEIF root AID.

**OOBI resolution:** To verify an issuer's signature, the issuer's Key Event Log must be fetched via an OOBI URL. This requires a live KERIA or witness endpoint.

## Resources

- [KERIpy](https://github.com/WebOfTrust/keripy)
- [vlei-verifier](https://github.com/GLEIF-IT/vlei-verifier)
- [vLEI trainings](https://github.com/GLEIF-IT/vlei-trainings)
- [ACDC spec](https://trustoverip.github.io/tswg-acdc-specification/)
