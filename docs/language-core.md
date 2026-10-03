# SENS language core — exact-domain identity

This document describes the current Contract 11 identity model.

Historical flat SENS8 / SID8 / Function8 descriptions remain useful as
provenance and compatibility evidence, but they are not current semantic
authority.

## Canonical semantic identity

A canonical SENS semantic object is:

```text
exact binary object
+ exact domain
+ proved / ratified law
```

Bits alone do not carry meaning. Width alone does not grant occupancy,
callability or semantic membership.

Equal packed payloads in different domains are distinct identities.

```text
D3 001 != D4 0001 != D5 00001 != D6 000001
```

No zero-padding, truncation, low-bit extraction or integer equality may create
or recover domain identity.

## Current ratified domain ladder

The current ratified exact-width language ladder is:

```text
D1  exact one-bit PredicateBit
D2  exact two-bit structural syntax
D3  exact three-bit Core foundation
D4  exact four-bit bootstrap
D5  exact five-bit typed domain
D6  exact six-bit typed domain
D7  exact seven-bit Sound7 / provenance domain
D8  exact eight-bit domain boundary
```

The ratified identity model requires a general domain carrier to preserve D1
through D8 exactly. Production cutover of that carrier is tracked by #2974;
implementation status must not be confused with ratification. Callable Core
identity is narrower: D1 and D2 are not callable domains; D7 keeps its Sound7
law and is not promoted into callable Core merely because it has a width; D8 is
distinct from historical Sens8/Function8 even though both occupy eight physical
bits.

Carrier existence, residency, derivability, callability and runtime
implementation are separate facts. Width alone never mints occupancy or a
semantic role. D5/D6/D8 residents execute only where their owning law admits
them, and a free coordinate has no meaning until such evidence exists.

## D1 — PredicateBit

```text
0 = NO
1 = YES
```

PredicateBit is not Number, host Bool, T/NIL or structural empty.

## D2 — structure

```text
00  separator
01  close
10  open
11  dot
```

These are structural-domain objects, not function identities.

## D3 — foundation

```text
000  structural empty ()
001  QUOTE
010  ATOM
011  COND
100  CONS
101  CAR
110  CDR
111  EQ
```

Role names above are documentation projections. The canonical identity is the
exact D3 coordinate under the D3 law.

## D4 — bootstrap

D4 is the exact four-bit bootstrap domain ratified by its owning law. Its
coordinates are not reconstructed from historical eight-bit Function8 values.

LAMBDA and DEFINE are current D4 bootstrap identities. Ratified selector
descendants are generated from their domain law rather than minted by legacy
table rows. Unallocated D4 coordinates remain unallocated.

## D5 / D6 — typed Core domains

D5 and D6 are exact-width typed domains. Their complete coordinate capacity is
not an automatic function table: only owner-ratified residents, proved
generators and implemented mechanisms may be used.

## D7 — Sound7

D7 is an exact seven-bit domain with its own Sound7 / textual-provenance law.
It may be carried by general domain identity, but it is not a callable Core
operation merely because it is seven bits wide. Selector geometry and generic
function-table rules must not be inferred for D7.

## D8 — exact eight-bit domain

D8 is an exact domain in the ratified ladder. It is **not** historical Sens8 or
Function8. Equal eight-bit payloads across those two contexts do not collapse
identity.

D8 residents are admitted only by explicit D8 law/evidence. Width eight does
not make every historical byte a D8 resident or callable operation.

## Reader

Canonical binary source preserves exact word width before semantic routing.

```text
10 001 01
```

is structurally D2 open, one exact W3 word, and D2 close. The canonical reader
model must preserve exact W1..W8 words as domain-qualified identity; production
support may advance domain-by-domain during the #2974 cutover. Callable lowering
is a later law-specific step: carrying a D1, D2 or D7 identity does not make it
a function.

The reader must never recover a domain by zero-extending an old eight-bit code.

Historical exact-eight-bit source remains a bounded compatibility path while
migration completes.

At expression start, apostrophe is reader sugar for the already-admitted D3
QUOTE identity; it must not create an intermediate human-name or Sens8
identity.

## Surfaces

Human-language and symbolic spellings are optional projections.

```text
surface/UI input
      ↓ mechanical registry projection
exact domain identity
```

where a domain mapping is admitted.

Unmigrated historical registry rows may still project explicitly to a legacy
eight-bit compatibility identity. That path must be named as legacy and must
not infer a domain from the byte.

Forbidden models include:

```text
name -> meaning
legacy byte -> guessed domain
width -> semantic role
```

## One active language core

SENS is returning to one active language core: `lib/core.lisp`.

Historical Core1 evidence is bootstrap/provenance. Core2 is retired
compatibility history. Core3 mechanisms belong to a mechanism laboratory.
The former Core4 name is folded into the one active core.

Execution/research profiles and backend choices may select mechanisms; they may
not create or override semantic domain law.

## Execution mechanisms

The Rust runtime is the **reference implementation**, not semantic authority.
C, Common Lisp, Prolog, Datalog, CLIPS, WASM, FPGA and other substrates are
additional mechanism witnesses.

A backend receives an already-selected domain-qualified semantic object or an
explicitly tagged compatibility projection. Backend opcodes, host enums,
packed bytes and native types never mint SENS meaning.

## Compiler / IR rule

Canonical compiler and IR identities preserve exact domain and exact bits.

A historical eight-bit ABI or fast path may remain only as an explicitly named
compatibility/backend projection. Reverse byte-to-domain inference is
forbidden.

## Structural empty is not zero in another domain

```text
D3 000 structural empty
!= D1 0 PredicateBit NO
!= Number 0
!= historical exact8 00000000
```

Equal packed numeric zero does not collapse domains.

## Historical Sens8 / Sid8 / Function8

Historical exact-eight-bit machinery may remain only in bounded roles:

- compatibility;
- transport;
- backend mechanism;
- archived provenance;
- explicit legacy external ABI.

It is not the universal semantic identity.

New canonical code must not add a Sens8/Sid8 dependency unless the boundary is
explicitly one of those roles.

## Project boundary

The Rust runtime is the reference implementation, not semantic authority.
Current authority is Contract 11 plus ratified domain laws and language-owned
executable evidence.

The current canonical source extension is **`.lisp`**. **`.wsm`** and
**`.my`** remain supported legacy aliases. File suffixes do not create
identity; exact source words and domain law do.

Authority precedence is documented in
[`semantic-authority-map.md`](semantic-authority-map.md).
