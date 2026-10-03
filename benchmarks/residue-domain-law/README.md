# #2662 — residue-domain law tournament

This benchmark starts after post-D4 root minimization.

Canonical input from #2617/#2655:

```text
PROVEN-ROOT       1  non-local-exit
CARRIER-PREMISE   4
POLICY-OVER-ROOT  2
```

The sole root deliberately remains:

```text
width      = UNKNOWN
coordinate = UNPLACED
```

## What this slice proves

It rejects two invalid domain-selection rules.

### R0 — smallest free domain

After OD-005 the current asymmetry is stronger:

```text
D5  32/32 historical residents / 0 unallocated
D6  has UNKNOWN/free capacity under the current closure map
```

So the naive rule "choose the smallest ratified domain with free capacity"
would now deterministically nominate D6. That still fails: the root theorem
supplies no width/domain membership law. **Unique availability is not semantic
evidence.**

### R1 — historical stratum

The canonical historical ledger records RETURN as present in Phase D, but also:

```text
current_domain_candidate = unresolved
binary_object             = unplaced
```

Chronology cannot be silently promoted into an exact-domain law.

## Open routes

```text
R2 semantic-fact lower bound
R3 independent root-domain law
R4 proof-addressed construction/projection
```

R4 alone cannot replace #2490 ontology:

```text
semantic object = binary number + exact domain + proved law
```

## Non-conclusions

- non-local-exit is not placed in D5;
- non-local-exit is not placed in D6;
- control-observation count does not imply bit width;
- D6 owner candidate `001111` is separate from this root-domain problem;
- no coordinate is allocated.

## Reproduce

```sh
python3 benchmarks/residue-domain-law/run.py --out /tmp/residue-domain-law
```
