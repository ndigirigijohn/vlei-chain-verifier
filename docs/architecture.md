# Architecture

## Overview

The verifier is a CLI tool built on [KERIpy](https://github.com/WebOfTrust/keripy). It performs offline verification of vLEI ACDC credentials — no server, no agent required for the core SAID and chain checks.

```
verifier.py
├── src/said.py        SAID recomputation and verification
├── src/acdc.py        credential parsing and edge extraction
├── src/schema.py      schema SAID verification (optional network)
├── src/chain.py       chain traversal and display
└── src/keystate.py    key state lookup and OOBI resolution
```

---

## The vLEI Trust Chain

vLEI credentials form a four-level hierarchy rooted at GLEIF. Each credential contains an edge (`e` block) pointing to its parent credential by SAID.

```
GLEIF Root AID  (trust anchor — known public AID)
      │
      │  issues
      ▼
  QVI Credential  (Qualified vLEI Issuer)
      │
      │  issues
      ▼
  LE Credential   (Legal Entity)
      │
      │  issues
      ▼
  ECR Credential  (Engagement Context Role)  ← leaf, held by a person
```

An ECR credential proves that a named individual holds a specific role (e.g. CFO) at a legal entity whose identity has been verified by a QVI accredited by GLEIF.

---

## What the Verifier Checks

### SAID Verification (offline)

Every ACDC has a `d` field — its **Self-Addressing Identifier**. A SAID is the Blake3-256 digest of the credential block, computed with `d` zeroed to a placeholder, then placed back inline. Any field modification invalidates the SAID.

```
credential bytes (d = "AAAA...") → Blake3-256 → base64url → "EJXsNi5W..."
```

This is verified by `src/said.py` using `keri.core.serdering.SerderACDC`.

### Schema SAID Verification (requires network)

The `s` field of a credential is the SAID of its JSON Schema document. The verifier fetches the schema from the GLEIF schema server and recomputes its `$id` SAID to confirm the schema has not changed. Handled by `src/schema.py`.

### Edge Chain Traversal (offline)

Each credential's `e` (edges) block contains named edges of the form `{"n": "<SAID>", "s": "<schema SAID>"}`. The verifier loads each credential file in order and follows the chain from leaf to root, verifying each SAID along the way. Handled by `src/chain.py`.

### GLEIF Root Detection (offline)

The chain terminates when the issuer AID of the root credential (QVI) is found in the known set of GLEIF root AIDs. `GLEIF_ROOT_AIDS` in `src/chain.py` holds this set.

### OOBI Resolution + Key State (requires live endpoint)

To verify that the issuer *signed* the credential with their current private key, the issuer's Key Event Log must be fetched via an OOBI URL. This connects to a live KERIA agent or witness. Handled by `src/keystate.py`.

---

## Data Flow

```
verifier.py
    │
    ├─ load_json(credential.json)
    │       │
    │       ▼
    │   parse_credential()  ──→  ACDCCredential
    │       │
    │       ├─ verify_said()          ← SerderACDC round-trip
    │       ├─ resolve_credential_type()
    │       └─ extract_edge_saids()
    │
    ├─ (--verify-schema)
    │       └─ fetch_and_verify_schema()  ──→  GET schema.vlei.dev/oobi/{said}
    │
    ├─ (--chain chain.json)
    │       └─ display_chain([ecr, le, qvi])
    │               └─ verify_chain()
    │                       ├─ verify_said()  ×3
    │                       └─ is_root_issuer check
    │
    └─ (--oobi URL)
            └─ resolve_oobi()
                    └─ Oobiery + runController  ──→  witness endpoint
```

---

## Module Responsibilities

| Module | Dependencies | Network? |
|---|---|---|
| `src/said.py` | `keri.core.serdering` | No |
| `src/acdc.py` | `dataclasses` | No |
| `src/schema.py` | `keri.core.coring`, `requests` | Optional |
| `src/chain.py` | `src/said`, `src/acdc`, `src/schema` | No |
| `src/keystate.py` | `keri.app.habbing`, `keri.app.oobiing` | Optional |

---

## KERIpy Internals Used

| KERIpy class / function | Purpose |
|---|---|
| `SerderACDC` | Parses and round-trip-verifies ACDC credentials |
| `Saider.saidify()` | Computes SAID for credential and schema sub-blocks |
| `Saider.verify()` | Verifies a SAID against a document |
| `habbing.openHby()` | Opens/creates an LMDB keystore as a context manager |
| `oobiing.Oobiery` | Doer that handles OOBI HTTP resolution |
| `directing.runController()` | Runs KERIpy's hio synchronous event loop |

**hio vs asyncio:** KERIpy uses `hio` — its own synchronous coroutine framework. There is no `async/await`. The OOBI event loop (`runController`) is a blocking call. Do not mix with `asyncio`.
