# Steady-phase cross-language bench (synergy with #3601 / #3608)

**Why:** #3601 currently measures only `phase=full` (cold one-shot).
The published ~2.656× CPython figure was **matched steady** `(repeat(N) − ready) / N`.
This suite adds that missing phase without forking `pareto_report.py`.

## Discipline

1. Correctness before any timing row.
2. Same workloads / params / expected answers as #3601 corpus.
3. Matched path: `ready` and `repeat N` share load+setup; only call count differs.
4. Primary metric: Cachegrind I refs when Valgrind present; wall is auxiliary.
5. Provenance JSON next to every TSV.
6. Do **not** relabel `full` ratios as steady.

## Workloads

| name | N | expected |
|------|--:|---------:|
| fib | 16 | 987 |
| loop | 700 | 1400 |
| ackermann | 3 | 61 |
| closures | 700 | 2100 |
| evenodd | 700 | 1 |

## Phases

| phase | meaning |
|-------|---------|
| `full` | process + load + one call (same as #3601) |
| `ready` | load + setup, **no** benchmark call |
| `repeat` | ready path + N benchmark calls |
| `steady` | derived: `(repeat − ready) / N` — never measured directly |

## Quick start

```bash
# Correctness only
python3 benchmarks/cross-language/steady/test_corpus.py

# Pure Python controls (no SENS binary)
python3 benchmarks/cross-language/steady/run_steady.py \
  --python-only --reps 3 --inner-reps 5 --out /tmp/steady-smoke

# With Valgrind I-refs (Linux)
python3 benchmarks/cross-language/steady/run_steady.py \
  --python-only --cachegrind --reps 3 --inner-reps 3 --out /tmp/steady-cg

# Full pair when SENS multi-mode runner exists
python3 benchmarks/cross-language/steady/run_steady.py \
  --sens-runner target/release/examples/current_exact_domain_bench \
  --reps 3 --inner-reps 3 --cachegrind \
  --out /tmp/steady-paired
```

Outputs join-friendly TSV (`runtime`, `workload`, `phase`, `i_refs` / `wall_s`) for `pareto_report.py`.

## Note on SENS runner

Until the #3601 binary exposes `ready`/`repeat` modes, `sens-exact` rows from this harness are `phase=full` only. CPython matched steady works today.
