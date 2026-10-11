# D8 NTH/MAPLIST × traversal direction — #3744

Status: **RESEARCH / UNRATIFIED**.

This experiment tests an independent `left | right` traversal axis for the current D6 `NTH | MAPLIST` family, derived from current D5 `REVERSE`.

## Direction law

```text
NTH-RIGHT(i,xs) = NTH(i, REVERSE(xs))

MAPLIST-RIGHT(xs,f)
  = MAPLIST(REVERSE(xs),
            lambda tail: f(REVERSE(tail)))
```

Reversing only the source is insufficient: each callback view must be conjugated too.

## Typed square

```text
                    left              right
indexed             NTH               NTH-RIGHT
all views           MAPLIST           MAPLIST-RIGHT
```

## Structural witness

```text
LEFT-VIEWS(xs)  = [xs, cdr(xs), cdr²(xs), ...]
RIGHT-VIEWS(xs) = map(REVERSE, LEFT-VIEWS(REVERSE(xs)))
```

For every valid index:

```text
NTH(i,xs)       = first(LEFT-VIEWS(xs)[i])
NTH-RIGHT(i,xs) = last(RIGHT-VIEWS(xs)[i])
```

Identity-view equality proves the exact view geometry before any common pure callback is post-composed.

## Finite exhaustive carrier

All bit lists over `{0,1}` of lengths 0..6:

```text
127 total lists
126 nonempty lists
642 valid indexed observations
```

Expected observability:
- NTH left/right differs in 300 indexed cases;
- MAPLIST view direction differs on 114 lists.

## Negative control

`MAPLIST(REVERSE(xs),f)` without reversing each callback view is incomplete conjugation. It must disagree with RIGHT-VIEWS on 114/126 nonempty lists, with 12 degenerate equal lists retained explicitly.

## Coordinate gauge

```text
D6 NTH     = 000100
D6 MAPLIST = 000101
D5 REVERSE = 10100
```

D8 footprint:

```text
00010000 00010001 00010010 00010011
```

`00` is the lower-domain NTH duplicate.  
`11` is the invariant generated MAPLIST-RIGHT candidate.  
The middle coordinates remain a gauge orbit containing MAPLIST and NTH-RIGHT.

## Reproduce

```sh
python3 benchmarks/d8-nth-maplist-direction/run.py \
  --out /tmp/d8-nth-maplist-direction
```

Expected research status: `PRODUCT-CANDIDATE-TYPED`.

No D8 resident, primitive, or callable mechanism is admitted here.
