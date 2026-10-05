# D8 RASSOC/ACONS × association orientation — #3741

Status: **RESEARCH / UNRATIFIED**.

This experiment asks whether the current D6 family

```text
RASSOC | ACONS
```

supports an independent second axis derived from pair transposition rather than coordinate aesthetics:

```text
tau((k,v)) = (v,k)
tau(A)     = map(tau,A)
```

Current D5 `ASSOC` supplies the already-ratified lower-domain key-query meaning.

## Typed square

```text
                    value-oriented     key-oriented
query               RASSOC             ASSOC
extend              ACONS              ACONS-SWAPPED
```

## Laws

```text
tau(tau(A)) = A

tau(RASSOC(q,A))
  = ASSOC(q,tau(A))

tau(ACONS(k,v,A))
  = ACONS(v,k,tau(A))
```

No-match query behavior is preserved exactly.

## Finite exhaustive carrier

Atoms are `{0,1,2}`, giving 9 ordered pairs. Enumerate all association lists of lengths 0..2 without repeated pair entries:

```text
1 + 9 + 9*8 = 82 alists
query cases     = 82 * 3 = 246
extension cases = 82 * 9 = 738
```

## Negative control

List-order reversal is tested as an arbitrary alternative involution. Over 729 nonempty extension witnesses it must fail to commute in 720 cases; the 9 degenerate equal cases are retained explicitly.

## Coordinate gauge

Current authority fixes:

```text
D6 RASSOC = 001100
D6 ACONS  = 001101
D5 ASSOC  = 11100
```

D8 footprint:

```text
00110000 00110001 00110010 00110011
```

`00` is the lower-domain RASSOC duplicate.  
`11` is the invariant generated ACONS-SWAPPED candidate.  
The middle coordinates remain a gauge orbit containing the lower-domain ASSOC and ACONS meanings.

## Reproduce

```sh
python3 benchmarks/d8-rassoc-acons-orientation/run.py \
  --out /tmp/d8-rassoc-acons-orientation
```

Expected research status: `PRODUCT-CANDIDATE-TYPED`.

No D8 resident, primitive, or callable mechanism is admitted here.
