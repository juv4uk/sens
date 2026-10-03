# SENS language core — binary domains, laws, and evidence

**Status:** CURRENT EXPLANATORY DOCUMENT · 2026-10-03

The previous SID8-only document has been preserved at
[`docs/archive/language-core-sid8-only-superseded-2026-10-03.md`](archive/language-core-sid8-only-superseded-2026-10-03.md).

This document summarizes the current model. It is not semantic authority by itself.
Use [`../CURRENT.md`](../CURRENT.md) and the referenced ratified/executable evidence.

## 1. Semantic object

Current owner paradigm (#2490):

```text
semantic object
=
binary number
+ exact semantic domain
+ proved/admitted law
```

Bits alone do not carry meaning.

The same bit string may legitimately appear in two domains and denote two different
semantic objects.

## 2. Domain, carrier, mechanism

Keep three layers separate:

```text
domain     = law-bearing semantic context
carrier    = concrete width/bit representation
mechanism  = executor/transport/substrate
```

Examples:

```text
D7.SoundCell [carrier=W7]       semantic domain
D7.LocalOrdinal [carrier=W7]    another semantic context
W7                              carrier only
Rust / FPGA / RF                mechanism only
```

A bare width is not enough to establish a semantic domain.

## 3. Core

Core reconstructs the historical Lisp line before deriving native SENS structure:

```text
Lisp I -> Lisp 1.5 -> later early-Lisp evidence
```

Research order (#2533):

```text
HISTORICAL-INGEST
        ↓
STRUCTURAL-DISCOVERY
        ↓
SENS-DERIVATION
```

The historical inventory must remain intact even when SENS later derives or
compresses an operation.

### Current domain status

| Domain | Current status |
|---|---|
| D1 | ratified PredicateBit |
| D2 | ratified structural racanā2 |
| D3 | ratified Core foundation |
| D4 | ratified Core foundation |
| D5 | ratified width/domain ontology; occupancy still under historical/structural research |
| D6 | ratified width/domain ontology; many coordinates remain deliberately UNKNOWN |
| D7 | ratified Sound7 + local śloka/sūtra ordinals; not arithmetic Number |
| D14 | research candidate: Pāṇini grammar graph |
| D24/D48/... | research candidates for exact Number / FPGA-friendly numeric domains |

Ratified width is not blanket occupancy.

## 4. Generated descendants

A generated child may earn its candidate identity from an exact parent plus an
admitted local generator:

```text
parent
+ delta / generator
-> generated child
```

Selector composition is the strongest current positive control.

For a selector-path coordinate, appending a semantic projection choice can agree
with the binary relation:

```text
E(extend(s,b)) = 2*E(s) + b
```

The arithmetic formula is not the semantic law by itself. The semantic law is
selector composition. #2502 cross-proves the current generated D4/D5 descendants
against an independent Core-Math executor.

## 5. Parentless roots and residue

A semantic root does **not** earn width from free space.

Current research distinguishes:

```text
roothood
width/domain membership
coordinate placement
```

These are separate claims.

For parentless roots such as the current non-local-exit control:

- roothood may be proved;
- exact width may remain UNKNOWN;
- coordinate may remain UNPLACED.

#2662/#2667/#2669 study how a parentless root can honestly earn an exact domain.

## 6. D6 PURE-UNKNOWN discipline

Unknown coordinates are not inventory defects.

A PURE-UNKNOWN D6 coordinate may leave that class only after a same-base semantic
law, lower-bound theorem, or other admitted placement evidence is established.

Forbidden placement arguments include:

- free capacity;
- numeric adjacency;
- attractive bit patterns;
- chronology alone;
- foreign Core-Math authority;
- mechanism-local metadata.

A successful research result may be **NO-CANDIDATE**.

## 7. Core-Math

Core-Math studies mathematical laws over binary objects independently of Core.

Minimal execution idea:

```text
binary input(s)
+ admitted mathematical law
-> binary output
```

Important evidence:

- #2491 — first minimal bounded `bits + law -> bits` executor;
- #2500 — exact-Q family/role factorization;
- #2509 — same machine transform in a different domain does not merge semantics.

Core-Math may diverge from Core. It does not inherit Core placement automatically.

## 8. Core / Core-Math relation

Three outcomes are admitted:

```text
DIVERGENT
COMPLEMENTARY
CONVERGENT
```

Convergence requires independent agreement on:

```text
binary object
+ exact domain
+ semantic equation
+ law
+ cross-proof
```

Matching syntax, names, hashes, ASTs, storage layouts, or machine formulas is not enough.

## 9. Human surfaces

Human names are source/UI projections.

This includes:

- Ukrainian;
- English;
- Sanskrit;
- symbolic spellings;
- historical Lisp names.

A name may help humans discuss an object. It does not replace the object's
binary-domain identity.

The canonical source extension remains **`.lisp`**. The suffix is a source/tooling
choice, not semantic identity.

## 10. Execution substrates

Rust is the current reference mechanism, not semantic authority.

The same rule applies to:

- C;
- Common Lisp;
- WASM;
- GraalVM;
- FPGA;
- GPU;
- Prolog / Datalog / CLIPS;
- radio/wire transports.

A mechanism may implement or carry an admitted object. It may not silently mint
new language meaning.

## 11. Wire and packed representation

Packed/wire representations preserve exact payloads and boundaries. They do not
create semantic domains.

Correct conceptual layering:

```text
semantic object
-> canonical SENS wire/container
-> transport framing
-> physical channel
```

CRC, FEC, ARQ, frequency, modulation and RF profile are transport mechanisms.

## 12. Governed research record

Current task grammar:

```text
PHASE
DOMAIN
BINARY OBJECT
LAW
WITNESS
FALSIFIER
STATUS
RELATION
```

Allowed PHASE values:

```text
HISTORICAL-INGEST
STRUCTURAL-DISCOVERY
SENS-DERIVATION
```

The schema makes uncertainty explicit; it does not auto-ratify semantics.

## 13. Historical SID8

The earlier flat 256-slot SID8/Function8 model remains:

- historical provenance;
- compatibility evidence;
- a migration donor;
- a useful falsifier against accidental return to flat identity.

It is **not** the current language ontology.

## 14. Project boundary

SENS owns admitted semantic meaning.

Reference implementations, generated files, benchmarks, surfaces, proof-address
formats and caches remain lower-level evidence/mechanism unless a separate law
explicitly promotes a fact.

Authority precedence:
[`semantic-authority-map.md`](semantic-authority-map.md).
