# D5 arithmetic product rectangle (#3349)

This probe keeps semantics independent from coordinates.

Exact-Q semantic product:

```text
family ∈ {additive, multiplicative}
role   ∈ {combine, right-quotient}
```

with:

```text
PLUS(a,b)       = a+b
DIFFERENCE(a,b) = a+(-b)
TIMES(a,b)      = a*b
QUOTIENT(a,b)   = a*(1/b), b != 0
```

Current D5 coordinates:

```text
PLUS        01010
DIFFERENCE  01011
TIMES       10110
QUOTIENT    10111
```

Observed coordinate axes:

```text
role_mask   = 00001
family_mask = 11100
```

The four coordinates form an affine XOR rectangle.

The executable oracle uses 93 reduced exact rationals and 8,649 ordered pairs.
QUOTIENT is undefined exactly on the 93 cases with zero second operand.

Anti-numerology is reported at several strengths:

- any affine rectangle among four labeled random D5 residents: 1/29;
- affine rectangle with any one-bit role axis: 5/899;
- fixed LSB role axis: 1/899;
- exact observed role+family masks: 1/26,970.

Therefore the semantic family×role law is strong, while the current coordinate
rectangle is only **bounded complementary bridge evidence**, not yet a forced
global coordinate law.
