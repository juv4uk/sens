# #1988 semantic-tree execution benchmark

Research-only benchmark for the proven CAR/CDR selector family.

It compares the same canonical selector words through:

- `flat`: dense predecoded table lookup;
- `cold`: decode `root + suffix` on every call;
- `cached`: decode distinct paths during preparation, reuse thereafter;
- `hybrid`: direct root arm plus generated-path cache/fallback branch.

The harness separates one-time preparation from execution. Cachegrind execution
cost is computed as `median(full) - median(prepare)`.

Correctness is checked before measurement: all four routes must return the same
tree node for the same workload.

Example smoke run:

```sh
python3 benchmarks/semantic-tree/run.py --smoke --out /tmp/sens-1988
```

Full bounded matrix:

```sh
python3 benchmarks/semantic-tree/run.py \
  --depths 0,1,2,4,8,16 \
  --patterns repeated,random \
  --calls 100000 --samples 3
```

The Rust binary is a mechanism model, not semantic authority. Semantic counters
(tree/prefix/generator/cache/registry operations) are reported independently of
CPU instruction counts.
