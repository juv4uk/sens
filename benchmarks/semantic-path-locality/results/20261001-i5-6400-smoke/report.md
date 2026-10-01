# #2009 — first semantic path locality result

Host: Intel Core i5-6400 @ 2.70 GHz, WSL2. Research-only mechanism benchmark.

Representative depth=16 execution results:

| locality | bit-walk I/call | flat I/call | cache I/call | cache hit rate |
|---|---:|---:|---:|---:|
| hot1 | 148 | 59 | 91 | 99.95% |
| hot16 | 148 | 59 | 92 | 99.20% |
| 80/20 | 148 | 59 | 116 | 79.45% |
| uniform | 148 | 59 | 211 | 0.65% |
| adversarial | 148 | 59 | 212 | 0.00% |

At depth=16 the perfect flat table also needs about 262 KiB of state and roughly 8.1 million setup I-refs in this harness.
The direct-mapped cache uses 8 KiB.

## Bounded observations

- cache performance is strongly workload-locality dependent;
- a cache that beats direct bit-walk on hot/80-20 traffic loses badly on uniform/adversarial traffic;
- perfect flat lookup is cheap per call but its state/preparation grows rapidly with depth;
- direct bit-walk is locality-insensitive and requires no table/cache state;
- therefore runtime cache must not be a default property of variable-width identity.

## Design implication

Static identities should be compiled away when possible. Dynamic identities should begin with a small direct bit-walk; caching should be a profile/workload decision, not semantic architecture.

Raw evidence: `summary.tsv` and `provenance.json` in this directory.