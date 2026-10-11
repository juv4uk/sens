# SENS semantic authority map

**Status:** CURRENT ARCHITECTURE MAP · 2026-10-03

The previous SID8-oriented map is preserved at
[`docs/archive/semantic-authority-map-sid8-superseded-2026-10-03.md`](archive/semantic-authority-map-sid8-superseded-2026-10-03.md).

## One rule

> Meaning is admitted by domain + law + evidence. Implementations, names and storage do not silently outrank that admission.

## Authority by claim type

SENS no longer treats every claim as if it were the same kind of authority.

### Owner/ratified architectural decisions

Examples:

- #2490 — binary-domain ontology;
- #2533 — historical-first Core phase order;
- #2414 — D5/D6 domain-width ratification;
- #2415 — D7 semantic-role/domain ratification.

These decisions define the current research frame until superseded.

### Machine-readable language/runtime authority

- `language-contract.lisp` for the observable runtime/language scope it covers;
- ratified machine-readable laws and guards;
- admitted conformance fixtures.

A stale machine-readable artifact is migration debt; it is not permission to ignore a newer explicit owner ratification.

### Executable evidence

- focused witnesses;
- falsifier harnesses;
- independent implementation parity;
- CI gates;
- counterexamples.

Executable evidence can prove or falsify a bounded claim. It does not automatically generalize beyond its declared scope.

### Reference mechanisms

- `crates/sens`;
- Rust/C/WASM/FPGA/GPU executors;
- parsers, compilers, caches, hashes, ASTs;
- wire/radio transports.

Mechanisms implement or carry semantics; they do not create semantic authority merely by existing.

### Documentation and generated projections

- README/CURRENT;
- generated tables;
- research reports;
- benchmark summaries.

These explain evidence and must point back to stronger sources.

### History/archive

- `docs/archive/**`;
- dated reports;
- superseded plans;
- old SID8/Core-profile documentation.

History is evidence of lineage, not current ontology.

## Current semantic identity

Canonical owner rule (#2490):

```text
semantic object
=
binary number
+ exact semantic domain
+ proved/admitted law
```

Therefore:

```text
bits alone             != meaning
width alone            != semantic domain
machine transform      != semantic law identity
human name             != canonical identity
free coordinate        != resident
hash/cache/registry    != semantic authority
```

## Domain is not carrier

#2540 separates:

```text
domain     = law-bearing semantic context
carrier    = exact bits/width representation
mechanism  = implementation/execution/transport
```

Example:

```text
D7.SoundCell [carrier=W7]
D7.LocalOrdinal [carrier=W7]
```

Both may use seven bits without becoming the same semantic domain.

## Current Core authority discipline

Core research follows #2533:

```text
HISTORICAL-INGEST
        ↓
STRUCTURAL-DISCOVERY
        ↓
SENS-DERIVATION
```

Historical presence is evidence about the historical language, not automatic proof of SENS fundamentality.

Structural compression may later explain several historical operations by one generator.

Native SENS placement is earned only after the historical sample and structural law are explicit.

## Placement authority

A binary coordinate may be admitted only when its placement is earned.

Examples of admissible evidence:

- exact parent + proved local generator;
- lower-bound theorem;
- independently stated root/domain law;
- owner ratification supported by explicit evidence.

Forbidden substitutes:

- free capacity;
- numeric proximity;
- aesthetically pleasing binary pattern;
- chronology alone;
- host metadata;
- foreign-domain bit transform.

D6 PURE-UNKNOWN is a positive example of refusing to allocate without law.

## Parentless roots

Roothood, width, and coordinate are separate claims.

A root may be semantically independent while its exact domain remains UNKNOWN.

Current residue-root research (#2662/#2667/#2669) exists precisely because:

```text
PROVEN-ROOT
!=
PROVEN-WIDTH
!=
PROVEN-COORDINATE
```

## Core-Math authority

Core-Math is independently governed by binary mathematical laws.

Minimal model:

```text
binary input(s)
+ admitted mathematical law
-> binary output
```

Core-Math does not inherit Core placement or historical Lisp authority.

Its proof/certificate/AST/hash/cache formats remain evidence/mechanism unless the semantic law itself says otherwise.

## Cross-domain firewall

#2508/#2509 are standing negative controls.

Selector-path and exact-Q group-factor structures can share:

```text
child = 2*parent + bit
```

while remaining different semantic laws in different domains.

Cross-domain application must fail closed.

## Core ↔ Core-Math convergence

#2495 admits:

```text
DIVERGENT
COMPLEMENTARY
CONVERGENT
```

A convergence claim needs:

```text
same binary object
+ same exact domain
+ same semantic equation
+ same law
+ independent cross-proof
```

#2502 is the bounded positive selector control.

A similar bit pattern or implementation formula is insufficient.

## Surfaces and historical names

Human names are projections:

- Ukrainian;
- English;
- Sanskrit;
- symbols;
- historical Lisp names.

They may be valuable explanation or source syntax, but do not own semantic identity.

## Host and transport boundary

Useful split:

```text
semantic object/law     -> SENS authority
execution               -> mechanism
authorization           -> trusted host boundary
wire/framing/RF         -> transport mechanism
```

Radio frequency, modulation, CRC, FEC and ARQ are not SENS semantic domains.

## Benchmark authority

Benchmarks measure mechanism cost.

They can compare:

- instruction counts;
- allocations;
- wire size;
- derivation work;
- cache behavior;
- closure growth.

They cannot prove semantic identity from speed.

Performance regression policy belongs in benchmark/CI documentation, not the semantic contract.

## Documentation rule

A current document must distinguish:

- ratified fact;
- executable bounded witness;
- research hypothesis;
- UNKNOWN/UNRESOLVED;
- historical record.

Do not rewrite old research documents merely to resemble current terminology. Preserve them and create/update the current explanatory layer.

The repository goal is not “one file contains truth.” The goal is **one explicit authority chain for every claim**.
