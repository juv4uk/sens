# SENS benchmarks and executable evidence

**Status:** CURRENT INDEX · 2026-10-03

The previous pre-domain performance document is preserved at
[`docs/archive/benchmarks-pre-binary-domain-2026-10-03.md`](archive/benchmarks-pre-binary-domain-2026-10-03.md).

This file is the current benchmark/evidence index. It deliberately separates
**semantic evidence** from **mechanism cost**.

## 1. Rule

> Correctness, law, domain and identity are not inferred from speed.

A benchmark may measure:

- instruction count;
- allocations;
- branches;
- packed/wire size;
- derivation work;
- closure growth;
- cache work;
- host/runtime cost;
- FPGA-oriented mechanism cost.

A benchmark does **not** promote a semantic law merely because one encoding is
faster or smaller.

## 2. CI policy

Prefer blocking CI on:

- semantic parity;
- fail-closed behavior;
- malformed-input rejection;
- exact-width preservation;
- deterministic replay;
- conformance fixtures;
- falsifiers that must continue to fail.

Hosted-runner wall time is usually noisy evidence. Collect it as an artifact or
diagnostic unless a benchmark has a controlled, justified regression threshold.

## 3. Current binary-domain evidence lanes

Representative current workflows:

### Domain and law structure

- `.github/workflows/binary-domain-format.yml`
- `.github/workflows/binary-domain-separation.yml`
- `.github/workflows/domain1234-dispatch.yml`
- `.github/workflows/generative-domain-forecast.yml`
- `.github/workflows/d5-selector-residue.yml`
- `.github/workflows/d6-pure-unknown-domain-firewall.yml`
- `.github/workflows/residue-domain-law.yml`
- `.github/workflows/root-domain-automorphism.yml`
- `.github/workflows/independent-root-domain.yml`

These lanes test placement/domain claims, not raw speed.

### Core-Math

- `.github/workflows/core-math-binary-exec.yml`
- `.github/workflows/core-math-binary-growth.yml`
- `.github/workflows/core-math-binary-seeds.yml`
- `.github/workflows/core-math-q-group-bits.yml`
- `.github/workflows/coordinate-monoid-research.yml`

These study `bits + domain + law -> bits`, generated operations, factor laws and
candidate mathematical structure.

### Core ↔ Core-Math

- `.github/workflows/core-coremath-selector-convergence.yml`
- `.github/workflows/binary-domain-separation.yml`

Use both positive and negative controls:

```text
same object + same domain + same semantics + same law
-> possible bounded convergence

same machine transform + different domain
-> no semantic convergence
```

### Foundation

- `.github/workflows/foundation-binary-substrate.yml`
- `.github/workflows/foundation-binary-word-law.yml`
- `.github/workflows/foundation-orientation.yml`
- `.github/workflows/foundation-ladder-bench.yml`
- `.github/workflows/foundation-compatibility-bench.yml`
- `.github/workflows/foundation-debt-ledger.yml`

Foundation experiments must state which premises are borrowed and which facts
are derived.

### Wire and human/manual transport

- `.github/workflows/numeric-wire-roundtrip.yml`
- `.github/workflows/human-wire-chunking.yml`
- `.github/workflows/human-wire-timing.yml`
- `.github/workflows/witness-presentation-wire.yml`

Wire/framing/RF are mechanisms. Their benchmarks must preserve semantic payload
without turning modulation/frequency/framing into domain identity.

## 4. Exact-width benchmark discipline

Every result must name enough context to be reproducible:

```text
workload
domain/carrier
implementation/substrate
machine
load context
size/depth
samples/repetitions
metric
semantic parity status
```

Do not compare rows that silently change domain, data type or workload shape.

## 5. Research benchmark interpretation

A research benchmark should say what kind of output it produces:

```text
WITNESS
FALSIFIER
BOUNDED-NEGATIVE
COUNTEREXAMPLE
MECHANISM-COST
SCALING-EVIDENCE
UNKNOWN
```

A bounded search failure is not automatically a theorem of impossibility.

A finite semantic signature match is not mathematical identity.

A successful host benchmark is not semantic ratification.

## 6. Closure/generation benchmarks

For law-generated operation/domain research, report at least:

- roots/premises;
- generator/law count;
- raw candidate count;
- type/domain rejects;
- identity/equivalence dedup;
- unique generated objects;
- semantic classes where measured;
- unresolved/UNKNOWN residue;
- search depth/budget;
- proof/certificate cost when applicable.

Do not hide combinatorial explosion.

## 7. Performance history

Older cold/warm interpreter numbers, rational-chain measurements, Python
comparisons and pre-domain SID8/function-table benchmarks remain valuable as
**historical mechanism measurements**.

They are preserved here:

[`docs/archive/benchmarks-pre-binary-domain-2026-10-03.md`](archive/benchmarks-pre-binary-domain-2026-10-03.md)

Do not use those measurements as evidence for the current binary-domain
ontology.

## 8. Current principle

**CI fails on semantic breakage. Performance evidence informs mechanism choices. Mathematics and executable laws decide semantic structure.**
