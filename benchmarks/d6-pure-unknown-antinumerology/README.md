# D6 PURE-UNKNOWN anti-numerology — #2664 lane C

This lane asks one narrow question:

> Can a coordinate-only property select a canonical resident from the 44
> `PURE-UNKNOWN` Core D6 slots?

The executable answer is **no** under the currently admitted evidence.

## Why

The merged #2660/#2661 frontier gives all 44 slots the same evidence class:

```text
PURE-UNKNOWN
canonical semantic member = false
placement ref             = empty
research refs             = empty
```

Therefore any permutation of the 44 coordinate labels that fixes the four
non-PURE frontier rows is class preserving.

The full symmetric action is transitive. Its invariant subsets are only:

```text
EMPTY
ALL-44-PURE-UNKNOWN
```

So there is no evidence-invariant singleton candidate.

## Concrete negative controls

The gate also attacks rankings based on:

- numeric coordinate order;
- Hamming weight;
- Hamming distance to `001111`;
- common-prefix proximity to `001111`;
- Hamming distance to the generated D6 selector set.

For each ranking, a transposition between two evidence-identical PURE-UNKNOWN
slots moves the preferred coordinate label to another abstract slot while no
semantic evidence changes.

Therefore each ranking is rejected as coordinate-label authority.

## Non-conclusion

This does **not** prove that the 44 slots can never receive residents.

It proves only:

```text
NO-CANDIDATE-FROM-COORDINATE-ONLY
```

A slot may leave PURE-UNKNOWN only after an independent semantic theorem breaks
the relabeling symmetry.

No width, coordinate, residency, or owner decision is made here.
