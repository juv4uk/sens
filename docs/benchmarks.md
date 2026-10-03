# Бенчмарки й executable evidence SENS

**Статус:** CURRENT INDEX · 2026-10-03

Попередній pre-domain performance document збережено в
[`docs/archive/benchmarks-pre-binary-domain-2026-10-03.md`](archive/benchmarks-pre-binary-domain-2026-10-03.md).

Цей файл — current index для benchmark/evidence lanes. Він навмисно розділяє
**semantic evidence** і **mechanism cost**.

## 1. Головне правило

> Correctness, law, domain та identity не виводяться зі швидкості.

Benchmark може вимірювати:

- instruction count;
- allocations;
- branches;
- packed/wire size;
- derivation work;
- closure growth;
- cache work;
- host/runtime cost;
- FPGA-oriented mechanism cost.

Benchmark **не** ратифікує semantic law лише тому, що encoding швидший або
менший.

## 2. CI policy

Blocking CI бажано будувати на:

- semantic parity;
- fail-closed behavior;
- malformed-input rejection;
- exact-width preservation;
- deterministic replay;
- conformance fixtures;
- falsifiers, які мусять продовжувати ламати хибний model.

Hosted-runner wall time часто шумний. Його слід збирати як artifact/diagnostic,
якщо немає окремо обґрунтованого controlled regression threshold.

## 3. Current binary-domain evidence lanes

### Domain і law structure

- `.github/workflows/binary-domain-format.yml`
- `.github/workflows/binary-domain-separation.yml`
- `.github/workflows/domain1234-dispatch.yml`
- `.github/workflows/generative-domain-forecast.yml`
- `.github/workflows/d5-selector-residue.yml`
- `.github/workflows/d6-pure-unknown-domain-firewall.yml`
- `.github/workflows/residue-domain-law.yml`
- `.github/workflows/root-domain-automorphism.yml`
- `.github/workflows/independent-root-domain.yml`

Ці lanes перевіряють domain/placement claims, а не raw speed.

### Core-Math

- `.github/workflows/core-math-binary-exec.yml`
- `.github/workflows/core-math-binary-growth.yml`
- `.github/workflows/core-math-binary-seeds.yml`
- `.github/workflows/core-math-q-group-bits.yml`
- `.github/workflows/coordinate-monoid-research.yml`

Тут досліджуються `bits + domain + law -> bits`, generated operations,
factor laws і mathematical structure.

### Core ↔ Core-Math

- `.github/workflows/core-coremath-selector-convergence.yml`
- `.github/workflows/binary-domain-separation.yml`

Треба мати і positive, і negative controls:

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

Foundation experiment має вказувати, які premises borrowed, а які facts
derived.

### Wire / human-manual transport

- `.github/workflows/numeric-wire-roundtrip.yml`
- `.github/workflows/human-wire-chunking.yml`
- `.github/workflows/human-wire-timing.yml`
- `.github/workflows/witness-presentation-wire.yml`

Wire/framing/RF — mechanisms. Benchmark має доводити збереження semantic
payload, а не робити modulation/frequency/framing частиною identity.

## 4. Exact-width benchmark discipline

Кожен результат має містити достатній reproducibility context:

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

Не порівнювати rows, які мовчки змінюють domain, data type або workload shape.

## 5. Як трактувати research benchmark

Research benchmark має назвати тип output:

```text
WITNESS
FALSIFIER
BOUNDED-NEGATIVE
COUNTEREXAMPLE
MECHANISM-COST
SCALING-EVIDENCE
UNKNOWN
```

Bounded search failure не є автоматично theorem of impossibility.

Finite semantic signature match не є mathematical identity.

Успішний host benchmark не є semantic ratification.

## 6. Closure/generation benchmark

Для law-generated domain/operation research звітувати щонайменше:

- roots/premises;
- generator/law count;
- raw candidate count;
- type/domain rejects;
- identity/equivalence dedup;
- unique generated objects;
- semantic classes, якщо виміряні;
- unresolved/UNKNOWN residue;
- search depth/budget;
- proof/certificate cost, якщо застосовно.

Combinatorial explosion не приховувати.

## 7. Performance history

Старі cold/warm interpreter numbers, rational-chain measurements, Python
comparisons і pre-domain SID8/function-table benchmarks лишаються корисними
**historical mechanism measurements**.

Вони preserved тут:

[`docs/archive/benchmarks-pre-binary-domain-2026-10-03.md`](archive/benchmarks-pre-binary-domain-2026-10-03.md)

Не використовувати їх як evidence для current binary-domain ontology.

## 8. Принцип

**CI падає на semantic breakage. Performance evidence допомагає вибирати mechanism. Mathematics і executable laws визначають semantic structure.**

## English · auxiliary

Current benchmark policy separates semantic evidence from mechanism cost.
Correctness/domain/law claims are gated by parity and falsifiers; noisy hosted
wall time is normally diagnostic evidence. Historical pre-domain benchmark
numbers remain archived and must not be used as proof of the current ontology.
