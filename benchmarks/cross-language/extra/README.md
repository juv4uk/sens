# Extra benches — startup isolation + amplification sweep

**Complements:** `benchmarks/cross-language/steady/`

## 1. Startup isolation (`startup/`)

Empty process only — no workload.

```bash
python3 benchmarks/cross-language/extra/startup/run_startup.py --reps 7 --out /tmp/startup
python3 benchmarks/cross-language/extra/startup/run_startup.py --cachegrind --reps 3 --out /tmp/startup-cg
```

## 2. Amplification sweep (`amplification/`)

`steady(N) = (median(repeat_N) − median(ready)) / N` for N ∈ {1,2,5,10,20,50}.

```bash
python3 benchmarks/cross-language/extra/amplification/run_amp.py --only fib,loop --out /tmp/amp
python3 benchmarks/cross-language/extra/amplification/run_amp.py --cachegrind --only fib --reps 1 --ns 1,3,5 --out /tmp/amp-cg
```

## Claim discipline

- Startup ≠ steady.
- Amplification tables are methodology evidence, not language rankings.
- Wall often needs large N; Cachegrind should be nearly flat across N.
