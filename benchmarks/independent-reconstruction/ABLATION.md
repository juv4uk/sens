# Reconstruction ablation benchmark

**Issue:** #2144  
**Parent harness:** #2138  
**Foundation:** #2107 #2103 #2112 #2117  
**Benchmark authority:** #1987

This benchmark asks which lower-evidence dimensions are necessary to recover the
bounded DAG semantics used by #2138.

It runs one full-evidence baseline, erases exactly one information dimension,
reconstructs again, and reports what changed.

## Ablations

- `deduplicate-evidence` — positive control; duplicate row multiplicity is
  non-semantic and must preserve the certificate and queries;
- `erase-relation-kinds` — preserve incidence but make all relation kinds
  anonymous;
- `merge-terminal-roles` — erase the distinction between two admitted terminal
  roles;
- `remove-one-incidence` — delete one unique semantic edge;
- `role-only` — retain roles, erase all relation edges;
- `relation-only` — retain typed relations, erase all local role distinctions.

## Run

```sh
python3 benchmarks/independent-reconstruction/ablation.py --smoke
python3 benchmarks/independent-reconstruction/ablation.py \
  --out /tmp/reconstruction-ablation/results
```

Outputs are TSV + JSON.

## Read the result correctly

A changed certificate proves only that the erased information mattered for this
bounded family.

An unchanged certificate is a **candidate redundancy result**, not deletion
authority. It must survive broader corpora and adversarial cases first.

The benchmark reports class/quotient-edge deltas and changed semantic query
answers separately. Timing is diagnostic only.
