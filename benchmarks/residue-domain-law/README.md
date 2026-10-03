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

Both ratified Core D5 and D6 have unused coordinates:

```text
D5  8 generated / 24 UNKNOWN-free
D6 16 generated / 1 ratified manual resident / 47 UNKNOWN-free
```

The same root theorem supplies no width. Free capacity is therefore
underdetermined even before applying `free coordinate != semantic membership`.

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
- owner-ratified D6 resident `001111` is separate from this root-domain problem;
- no coordinate is allocated.

## Reproduce

```sh
python3 benchmarks/residue-domain-law/run.py --out /tmp/residue-domain-law
```
