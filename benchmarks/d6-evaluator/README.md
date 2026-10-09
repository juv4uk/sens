# D6 selector real-evaluator replay (#3583)

Phase 1 measures the current 16 D6 selector words through the **real SENS
evaluator** using already-prepared exact-domain AST nodes.

Controls:
- `d6` — one exact D6 DomainCall, executed by the current selector law;
- `d3-chain` — the same selector semantics expanded into four nested exact D3
  CAR/CDR DomainCall nodes;
- `quote-only` — the shared exact D3 QUOTE/data argument cost.

No human function names participate in the prepared call path. No production
flat16 table is added.

Run:

```sh
python3 benchmarks/d6-evaluator/run.py \
  --calls 20000 --samples 3 \
  --out /tmp/sens-3583
```

Correctness is checked first for all 16 D6 coordinates against both the exact
D3 composition and an independent binary-tree oracle.

Instruction references and branch counts are phase-subtracted because they are
additive. Cache/predictor misses are reported as prepare/full totals only.

This phase does **not** claim a flat16-vs-generator evaluator comparison. A
future flat16 evaluator control is admissible only behind an explicit
benchmark-only compile hook that is disabled by default.
