# D8 cheap second-axis collapse screen — #3669

This research falsifier rejects tempting second axes that do **not** earn a
four-corner D8 product.

It allocates no D8 coordinate and uses no historical D8 donor.

## Screened axes

Five D6 families receive a cheap, independently stated candidate second axis:

| D6 family | proposed second axis | result |
|---|---|---|
| LENGTH / LENGTH-ONTO | list reversal | AXIS-INVISIBLE |
| MIN-LIST / MAX-LIST | numeric-negation conjugation | AXIS-DEPENDENT |
| ADD1 / SUB1 | numeric-negation conjugation | AXIS-DEPENDENT |
| INTEGERP / RATIONALP | numeric negation | AXIS-INVISIBLE |
| REMAINDER / GCD | argument swap | PARTIAL-COLLAPSE |

### LENGTH / LENGTH-ONTO

For every binary list of length 0..5 and several accumulator values:

```text
LENGTH(reverse(xs)) = LENGTH(xs)
LENGTH-ONTO(reverse(xs), a) = LENGTH-ONTO(xs, a)
```

The orientation axis is invisible.

### MIN-LIST / MAX-LIST

Over all non-empty lists of length 1..4 with elements in `[-2,2]`:

```text
NEG(MIN(NEG(xs))) = MAX(xs)
NEG(MAX(NEG(xs))) = MIN(xs)
```

Negation merely reproduces the existing MIN/MAX family toggle. The proposed
second axis is therefore dependent on the first.

### ADD1 / SUB1

For integers `[-32,32]`:

```text
NEG(ADD1(NEG(x))) = SUB1(x)
NEG(SUB1(NEG(x))) = ADD1(x)
```

Again, negation is the same semantic toggle as the existing family axis.

### INTEGERP / RATIONALP

Across 23 distinct exact rationals generated from numerators `[-4,4]` and
denominators `[1,4]`:

```text
INTEGERP(-x) = INTEGERP(x)
RATIONALP(-x) = RATIONALP(x)
```

The proposed sign axis is invisible.

### REMAINDER / GCD

Across 256 positive integer pairs `1..16 × 1..16`:

- `GCD(a,b) = GCD(b,a)` on every pair;
- REMAINDER changes under argument swap in 240 cases;
- the four putative corner functions produce only **3 unique truth tables**.

Therefore the square partially collapses.

## Interpretation

Expected summary:

```text
families screened    5
surviving axes       0
axis-invisible       2
axis-dependent       2
partial-collapse     1
```

This eliminates only the **tested axis**. A family may still support a
different independently proved D8 axis.

The practical value is search reduction: agents should not reopen these five
specific hypotheses as D8 product candidates.
