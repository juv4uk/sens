# #2009 Semantic path locality / entropy benchmark

Research-only benchmark. No production SENS runtime or semantic authority is changed.

The benchmark holds selector semantics and depth fixed while changing **reuse shape**:

- `hot1` — one path repeated;
- `hot16` — small stable working set;
- `mix80` — deterministic 80/20 hot/cold mix;
- `uniform` — deterministic uniform-like stream;
- `adversarial` — paths selected to collide in a 1024-entry direct-mapped cache when depth permits.

It compares:

1. direct root+suffix bit-walk;
2. perfect flat table lookup;
3. direct-mapped runtime cache whose miss path is the same bit-walk.

Cachegrind `I refs` are measured with cache/branch simulation disabled. Setup is measured separately from execution so flat-table preparation is not hidden inside the per-call number.

Run:

```sh
python3 benchmarks/semantic-path-locality/run.py --calls 50000 --reps 3
```

Outputs:

- `summary.tsv` — execution/setup/state/hit-rate matrix;
- `provenance.json` — host/toolchain provenance.

The architectural question is deliberately narrow: **does a cache win because the mechanism is good, or only because the benchmark happens to repeat the same identity?**