# #2113 deterministic logical smoke — 2026-10-01

This is machine-independent logical accounting from the benchmark model, not a CPU performance result.

## Strong bounded findings

- **chain / cycle:** compatibility witnesses recover 100% of true boundary equalities with zero residual facts.
- **fan-out / fan-in:** compatibility witnesses recover 0% of shared-source/shared-target equalities. The missing facts are not false; they are UNKNOWN.
- **mixed:** compatibility recall decreases as unwitnessed same-side incidence dominates:
  - n=8: 60.0%
  - n=32: 21.1268%
  - n=128: 5.9716%
  - n=512: 1.5444%
- **one_state:** compatibility is information-complete, but storage explodes quadratically:
  - n=32: 1,024 compatibility facts vs 64 explicit boundary labels;
  - n=128: 16,384 vs 256;
  - n=512: 262,144 vs 1,024.
- The hybrid model reaches 100% positive-equality recall in every workload with zero false positives by adding only the residual equality witnesses that compatibility cannot derive.

## Interpretation

There is no single monotone win from moving downward to compatibility facts.

Two independent failure modes exist:

```text
sparse compatibility:
  cheap facts
  but missing semantic incidence -> UNKNOWN

dense compatibility:
  complete information
  but O(n^2) fact/storage pressure
```

So the relevant benchmark vector is at least:

```text
(stored facts,
 recovered semantic facts,
 UNKNOWN/residue,
 setup instructions,
 query instructions)
```

No weighted winner is implied. Cachegrind replication is delegated to the CI workflow in this branch.
