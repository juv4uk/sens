# D8 REDUCE/SCAN × fold direction — #3674

This is a research-only D8 product witness on the **nonempty-list lane**.

It does not admit a D8 resident or change runtime callability.

## Current inputs

- D6 REDUCE/SCAN law: #3370;
- D6 owner-ratified coordinate authority: #3393;
- D5 REVERSE authority: #3305;
- D6 FLIP semantics: #3393 / #3384;
- D8 remains research: #3281.

No historical D8 donor is used.

## Two axes

Existing D6 family axis:

```text
exposure = REDUCE | SCAN
```

Candidate second axis:

```text
fold direction = left | right
```

Definitions on nonempty lists:

```text
REDUCE-right(f,z,xs)
  = REDUCE-left(FLIP(f), z, REVERSE(xs))

SCAN-right(f,z,xs)
  = SCAN-left(FLIP(f), z, REVERSE(xs))
```

The right SCAN is reported in computation order. This preserves the existing
family law:

```text
last(SCAN-right) = REDUCE-right
```

## Exhaustive finite carrier

Use bit carrier `{0,1}`.

There are exactly **16** binary functions `{0,1}² -> {0,1}`.
The witness enumerates all of them, both initial accumulator bits, and every
nonempty bit-list of lengths 1..4.

```text
16 operations × 2 initial bits × 30 lists = 960 cases
```

Results:

```text
left  last(SCAN)=REDUCE       960 / 960
right last(SCAN)=REDUCE       960 / 960

direction observable, REDUCE  264 cases
direction observable, SCAN    600 cases
multi-step SCAN history       896 cases
```

Negative controls:

```text
reverse the correct right-SCAN output:
  terminal law fails          296 cases

reverse input but omit FLIP:
  differs from right fold     216 cases
```

So direction is not a decorative relabel.

## Coordinate/gauge result

Current D6 authority resolves:

```text
D6 REDUCE = 101110
D6 SCAN   = 101111
```

Candidate family:

```text
10111000
10111001
10111010
10111011
```

It has zero collision with the 64 selector research candidates.

With base/base anchored at REDUCE-left:

- `10111000 = REDUCE-left` is a lower-domain duplicate;
- the middle `01/10` orbit contains lower-domain SCAN-left and generated
  REDUCE-right;
- **`10111011 = SCAN-right`** is invariant under axis-order swap.

## Explicit boundary

#3370 pins `last(SCAN)=REDUCE`, but does not fully specify the empty-list
presentation of SCAN.

Therefore this witness is deliberately classified:

```text
PRODUCT-CANDIDATE-NONEMPTY
```

It does not silently invent empty-list semantics. A later authority decision
can either extend or falsify this candidate at that boundary.

## Reproduce

```sh
python3 benchmarks/d8-reduce-scan-direction/run.py \
  --out /tmp/d8-reduce-scan-direction
```
