# #1973 — Pareto vector from published domain benches

**Agent:** grok-xai  
**Nature:** consumer / synthesis — **not** a new Cachegrind primary harness  
**Raw rows:** `1973-pareto-from-published.tsv`

## Why this exists

#1988 / #1989 / #1993 measure **different axes**. Whole-model accounting must not average C/Rust absolute I-refs. It must keep a **vector** and mark each claim:

| class | meaning |
|-------|--------|
| replication-invariant | ≥2 independent harnesses or mechanical law |
| single-harness | one image/implementation |
| single-harness-only | provisional (e.g. 1-sample smoke) |

## Machinery ledger (from #1973 first result)

| model | explicit rows | generator actions | coverage | identities deleted |
|-------|--------------:|------------------:|----------|-------------------:|
| flat donor | 34 | 0 | 34/34 | 0 |
| root+path | 8 | 2 | 14/34 | 0 |
| hybrid (unresolved explicit) | 28 | 2 | 34/34 | 0 |

```text
execution rows avoided = 6
semantic identities eliminated = 0
```

Path compresses **mechanism**, not meaning.

## Execution route (#1988)

**Invariant:** cold root+suffix beats flat at every measured depth; hash-cache does not beat cold; flat prepare ~2^k.

**Not invariant:** absolute I-ref scale; flat vs cache secondary ordering.

## Carrier (#1989)

**Invariant:** Inline64 fails universality at 64→65.

**Single-harness:** Sens8 cheapest 8-bit EQ; spill boundary pays alloc.

## Framing (#1993)

**Invariant:** zero-pad EOS falsified (#1980).

**Provisional smoke:** Width3 cheaper on short words; container ~+8 I/msg; outer-gamma expensive.

## Generator economy (this PR microbench)

| candidate | rules | descendants | rows avoided | economy |
|-----------|------:|------------:|-------------:|--------|
| CAR/CDR suffix 0/1 | 2 | 6 | 6 | **pass** |
| one-off ATOM→NULL style | 1 | 1 | 1 | **weak** — not automatic prefix allocation |

Matches #1973 design idea: semantic proof ≠ economy proof.

## Decision boundary (no weighted winner)

```text
semantic model:     root+suffix supported for selectors
interpreter:        direct decode > lookup/cache (bounded)
compiler:           compile path away — UNMEASURED (cml#397)
wire decode:        cost provisional (#1993 matrix)
carrier:            short fast path useful; universal box open
```

## What this PR does **not** claim

- production cutover
- averaging harness I-refs into one score
- that hybrid is “done” while 20 nodes unresolved
