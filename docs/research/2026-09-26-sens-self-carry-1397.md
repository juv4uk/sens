# SENS self-carry experiment #1397 — exact function across two stages

Date: 2026-09-26  
Branch: `research/1397-exact-sens-self-carry`  
Parent research: #1397 / #1383

## Question

Can a SENS function cross one language stage and become the executable head of the
next stage **without** a round trip through a human name, string, quoted symbol,
decimal/hex representation, or backend semantic enum?

The bounded experiment uses `00000101` because it already has an admitted callable
mechanism in the root runtime. The carrier is an exact lambda written as
`00001000`, not a named helper.

## Executable path

```text
00000101
   ↓
((00001000 (f) f) 00000101)        stage A
   ↓
exact runtime value 00000101
   ↓
(((00001000 (f) f) 00000101)
  (00000001 (alpha beta)))          stage B
   ↓
alpha
```

The Rust witness inspects stage A as the current runtime representation
`Value::Sid(Sens8)` and requires its payload to equal `sens!(00000101)`.
That Rust variant name is implementation vocabulary only; the experiment does not
introduce a second language identity above the eight bits.

No Core loader is called. The session stays at
`selected_core_profile() == None` before and after the two-stage execution.

## Fail-closed control

The same carrier transports `11111111` unchanged:

```text
11111111 → stage A → exact 11111111 → stage B call
```

Stage B fails with the existing named error:

```text
SENS function has no admitted callable mechanism: 11111111
```

So failure occurs because the exact function has no admitted callable mechanism,
not because its identity was lost or reconstructed incorrectly.

A seven-bit lookalike `1111111` is the negative control. The canonical parser
reads it as the exact decimal number `1111111`, the identical carrier closure
returns that number, and stage B fails with `expression is not callable`.
It never reaches SENS mechanism admission. This separates function-space membership
from transport success.

## What this proves

- an exact SENS function can be a first-class value;
- stage A returns the same exact function representation it received;
- stage B can directly use that returned value as an executable head;
- the witness source performs no function-name → SENS conversion;
- no string, quoted-symbol, decimal, hexadecimal, or semantic-enum identity carrier is used;
- an unsupported exact function stays exact and fails closed at mechanism admission;
- an exact-looking token outside the eight-bit function space follows a different,
  ordinary-value failure path;
- the experiment needs no Core profile selection and changes no production semantics.

## Explicit limit

`Session::default()` installs the normal root builtin environment, whose implementation
is compiled together with the generated registry projection. The current public test API
does not expose a production-neutral way to physically remove every root surface binding
or compiled registry table.

Therefore this first slice proves **no surface source/library lookup is required by the
two-stage exact path**; it does not claim that the compiled runtime projection was
physically absent from the process. A stronger “surface tables physically removed”
fixture would require a separate bounded test hook or substrate witness and must not be
smuggled into this research PR as a production runtime change.

## Non-goals

- no resurrection of deprecated `Sid8` as language ontology;
- no named primitive table;
- no `CanonicalIdentity` / `NecessaryFormIdentity`;
- no historical Core1 semantics rewrite;
- no automatic production migration from this result.

This is evidence for #1383 only.
