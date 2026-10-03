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

## Current Core domains

The current exact-width Core family includes:

```text
D1  exact one-bit predicate answers
D2  exact two-bit structural syntax
D3  exact three-bit foundation
D4  exact four-bit bootstrap
D5  exact five-bit typed domain
D6  exact six-bit typed domain
```

D5/D6 carrier existence, residency, derivability, callability and runtime
implementation are separate facts. A free coordinate has no meaning until its
owning law admits it.

D7 sound/text work is separate and is not callable merely because it is binary.

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

LAMBDA and DEFINE are current D4 bootstrap identities. Unallocated D4
coordinates remain unallocated.

## Reader

Canonical binary source preserves exact word width before semantic routing.

```text
10 001 01
```

is structurally D2 open, one exact W3 word, and D2 close. A source-domain bridge
may lift admitted W3/W4/W5/W6 words directly into their exact Core domains.

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

Rust, C, Common Lisp, Prolog, Datalog, CLIPS, WASM, FPGA and other substrates
are mechanism witnesses.

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

The Rust reference implementation is evidence and mechanism, not semantic
authority. Current authority is Contract 11 plus ratified domain laws and
language-owned executable evidence.

The canonical source extension remains **`.lisp`**. File suffixes do not
create identity; exact source words and domain law do.

Authority precedence is documented in
[`semantic-authority-map.md`](semantic-authority-map.md).
