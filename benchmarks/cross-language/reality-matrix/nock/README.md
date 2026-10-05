# Nock reality lane (#3685)

This lane must keep **three different questions separate**.

## A. Machine minimality

Pinned source of truth: Nock 4K specification.

- Official spec: https://docs.urbit.org/nock/specification
- Nock formulas use instruction atoms 0..11.
- The full reduction system also contains noun/data rules and the primitive operators
  used by the instruction definitions.

Do not reduce "machine size" to the number 12 alone. Record:
- instruction forms;
- primitive reduction operators/rules;
- data model;
- evaluator/spec text footprint under a documented counting rule.

## B. Serialized program size

Pinned source of truth: Urbit noun serialization.

- Official serialization docs: https://docs.urbit.org/hoon/serialization
- Nock code is a noun.
- The canonical compact transport baseline is `jam`/ `cue`.
- Newt is a framed transport and must be reported separately from raw jam bits.

First matched controls should map the existing D3 smoke observables to explicit
`[subject formula]` nouns and compare:
- SENS exact semantic bits;
- SENS production packed bytes;
- Nock jam bit length / byte container;
- optional Newt framed bytes as a separate transport row.

The noun mapping itself must be published; atom 0 is only a benchmark representation of
the fixture's empty observable, not a claim of SENS/Nock semantic identity.

## C. Runtime performance

Pinned implementation family: Vere.

- Runtime repository: https://github.com/urbit/vere
- Vere does not simply execute the 47-line spec text; it builds/executes an internal
  bytecode and has jets/optimized runtime mechanisms.

Therefore a Python or ad-hoc evaluator in this repo may be used only as a correctness
oracle/falsifier. It MUST NOT produce the Nock runtime performance verdict.

A runtime row needs:
- pinned Vere release/commit;
- build flags;
- exact noun input;
- jet policy;
- warm/cold distinction;
- same-machine raw evidence.

## Semantic-density rule

Nock machine minimality and SENS law-generated semantic density are different axes.

For SENS, keep the Reality Matrix tuple:
`independent_roots, independent_laws, derived_residents, admitted_residents_in_scope`.

For Nock, record the corresponding minimal machine/spec facts without inventing a
"derived resident" concept that Nock itself does not have. No magic combined score.

## First deliverable

Before any speed claim:
1. pin spec/serialization/runtime versions;
2. implement or call a jam encoder with official test vectors;
3. publish the exact matched noun mapping for the two D3 controls;
4. compare raw artifact sizes;
5. only then decide whether building pinned Vere is worth the runtime slice.
