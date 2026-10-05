# D8 cheap second-axis collapse screen — #3669

This research witness rejects tempting but non-independent second axes before
they can become D8 coordinate claims.

It allocates no D8 coordinates and does not consult the historical D8 donor.

## Screened proposals

| D6 family | proposed second axis | result |
|---|---|---|
| LENGTH / LENGTH-ONTO | list reversal | AXIS-INVISIBLE |
| MIN-LIST / MAX-LIST | numeric-negation conjugation | AXIS-DEPENDENT |
| ADD1 / SUB1 | numeric-negation conjugation | AXIS-DEPENDENT |
| INTEGERP / RATIONALP | numeric negation | AXIS-INVISIBLE |
| REMAINDER / GCD | argument swap | PARTIAL-COLLAPSE |

Exact bounded results:
- LENGTH(reverse(xs)) = LENGTH(xs): 63/63
- LENGTH-ONTO reversal invariance: 315/315
- NEG∘MIN∘NEG = MAX and NEG∘MAX∘NEG = MIN: 780/780 each
- NEG∘ADD1∘NEG = SUB1 and NEG∘SUB1∘NEG = ADD1: 65/65 each
- INTEGERP/RATIONALP invariant under negation over 23 exact rationals
- GCD symmetric on 256/256 positive pairs while REMAINDER changes on 240/256, leaving only 3 unique corners

Result: **0/5 proposed axes survive**.

This eliminates axes, not whole D6 families.

Reproduce:

```sh
python3 benchmarks/d8-collapse-screen/run.py --out /tmp/d8-collapse-screen
```
