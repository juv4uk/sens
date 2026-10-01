# Generator economy microbench

**Parents:** #1973 · #1987 · #1961  
**Not:** #1988 execution harness · #1989 carrier · production

## Question

Does a local generator **earn** a prefix bit on economy, or only on semantic validity?

```text
semantic proof  → candidate
economy proof   → allocation pressure
```

## Models compared (counts only)

### CAR/CDR family (positive control)

```text
roots: 101 CAR, 110 CDR
suffix actions: 0 → inner CAR, 1 → inner CDR
descendants measured: caar cadr cdar cddr + second/third aliases as *mechanism* share only
```

### One-off rule (stress)

```text
1 rule → 1 child → 1 explicit row avoided
```

Representative of ATOM→NULL style candidates that may be semantically interesting but fail compression.

## Metric

```text
economy_ratio = rows_avoided / max(rule_count, 1)
```

No Cachegrind here — machinery ledger only. CPU cost lives in #1988.

## Run

```sh
python3 benchmarks/generator-economy/run.py
```

Writes `docs/research/1973-generator-economy.tsv` when run from repo root (or stdout).
