# Credential Format

## ACDC Structure

An ACDC (Authentic Chained Data Container) is a JSON document. Every field at the top level is either a SAID (cryptographic digest) or a block with its own SAID.

```json
{
  "v":  "ACDC10JSON00028e_",
  "d":  "EKVR6fidbnBbw9je6pPbdIrXSEDHwX-CXYVwu_uU6upg",
  "i":  "EA4C5U10VgXCCvQtnioj-Nuc7Ey5dNQwHVMNWDhPj6hw",
  "ri": "EBfMDFWxNHYCQ4jbTnmFMwc2N2gHbA6N8LF1LFkpGMek",
  "s":  "EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw",
  "a":  { ... },
  "e":  { ... }
}
```

### Top-level fields

| Field | Name | Description |
|---|---|---|
| `v` | version | Protocol, serialisation kind, and byte size: `ACDC10JSON<size>_` |
| `d` | SAID | Self-Addressing Identifier — Blake3-256 digest of this credential |
| `i` | issuer | AID of the entity that issued this credential |
| `ri` | registry | SAID of the Transaction Event Log (TEL) tracking issuance/revocation |
| `s` | schema | SAID of the JSON Schema document defining this credential type |
| `a` | attributes | The claims block (who the credential is about and what it asserts) |
| `e` | edges | Links to parent credentials in the trust chain |
| `r` | rules | Legal or policy text (optional) |

---

## The Attributes Block (`a`)

The `a` block has its own `d` SAID and contains the subject claims:

```json
"a": {
  "d":  "EOr_lFWjETw6-aMDNTiP2HxPGcRiJM_zysDPBAojwbfa",
  "i":  "EL-4W7KYbBf7I-EzrXBoiVAyegbFJalQwC6CopSUhC4B",
  "dt": "2024-01-15T12:00:00.000000+00:00",
  "LEI": "254900OPPU84GM83MG36",
  "personLegalName": "Jane Smith",
  "engagementContextRole": "Chief Financial Officer"
}
```

The `i` field inside `a` is the **subject AID** (who the credential is about). The `i` field at the top level is the **issuer AID** (who issued it).

---

## The Edges Block (`e`)

The `e` block links this credential to parent credentials by SAID:

```json
"e": {
  "d":  "EM1kUYSehqp4vIzZGvFVC3MEisTS3ge1OYjWqvjEarHZ",
  "le": {
    "n": "EJcd4KY_LIdReU1WNLtpcPYJu7QNLt-DK6x5OBS8TFAl",
    "s": "ENPXp1vQzRF6ELV5kl2uraw4MrmsTXgng1xdt4n2pHfn"
  }
}
```

| Field | Description |
|---|---|
| `d` | SAID of the edge block itself |
| `le` / `qvi` | Named edge (the name indicates the relationship) |
| `n` | SAID of the referenced (parent) credential |
| `s` | Schema SAID of the referenced credential |

The verifier extracts the `n` values to follow the chain upward.

---

## vLEI Credential Types

The credential type is identified by the `s` (schema) field. Known schema SAIDs for the GLEIF testnet:

| Type | Full Name | Schema SAID |
|---|---|---|
| QVI | Qualified vLEI Issuer | `EBfdlu8R27Fbx-ehrqwImnyjnB2YpMgOEOs9OkdeKFzw` |
| LE | Legal Entity | `ENPXp1vQzRF6ELV5kl2uraw4MrmsTXgng1xdt4n2pHfn` |
| OOR | Official Organizational Role | `EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy` |
| ECR | Engagement Context Role | `EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw` |

These are version-specific. Verify against the [GLEIF testnet schema server](https://schema.vlei.dev) before use in production.

---

## SAID Encoding

SAIDs use CESR (Composable Event Streaming Representation) base64url encoding. The first character encodes the derivation code:

| Prefix | Derivation |
|---|---|
| `E` | Blake3-256 digest |
| `D` | Ed25519 public key |
| `B` | Ed25519 public key (non-transferable) |

An `E`-prefixed SAID is 44 characters and encodes 32 bytes of Blake3-256 digest in modified base64url (no padding, `-` and `_` instead of `+` and `/`).

---

## Chain File Format

The `chain.json` manifest tells the verifier where to find each credential in the chain and what the GLEIF root AID is:

```json
{
  "files": [
    "fixtures/sample_ecr.json",
    "fixtures/sample_le.json",
    "fixtures/sample_qvi.json"
  ],
  "gleif_root": "EGzi85A91B597MOBqgBoJTkyvWHhRSO-UWooYKEosk6c"
}
```

Files must be ordered leaf-first (ECR → LE → QVI). The `gleif_root` AID is added to the hardcoded `GLEIF_ROOT_AIDS` set at runtime — this allows using generated or testnet chains without modifying source code.

---

## Resources

- [KERIpy](https://github.com/WebOfTrust/keripy) — Python implementation of KERI
- [WebOfTrust/vLEI](https://github.com/WebOfTrust/vLEI) — vLEI specification and schema sources
- [vlei-verifier](https://github.com/GLEIF-IT/vlei-verifier) — GLEIF's production verifier
- [ACDC specification](https://trustoverip.github.io/tswg-acdc-specification/) — Trust over IP ACDC spec
- [GLEIF testnet schema server](https://schema.vlei.dev) — live schema SAID lookup
