# D8 ZIP/UNZIP × product orientation — #3710

This is a research-only typed D8 product witness. It does not admit a D8
resident and does not change runtime callability.

## Current inputs

- D6 ZIP/UNZIP law: #3370;
- D6 owner-ratified coordinate authority: #3393;
- D8 remains research: #3281.

No historical D8 donor is used.

## Two axes

Current D6 typed role axis:

```text
constructor = ZIP
destructor  = UNZIP
```

Independent orientation axis:

```text
normal | swapped
```

Derived meanings:

```text
ZIP-SWAPPED(xs,ys) = ZIP(ys,xs)
UNZIP-SWAPPED(ps)  = swap(UNZIP(ps))
```

Typed square:

```text
                    normal          swapped
constructor         ZIP             ZIP-SWAPPED
destructor          UNZIP           UNZIP-SWAPPED
```

## Exhaustive finite witness

Carrier: bit lists over `{0,1}`, equal-length lane, lengths 0..4.

The number of ordered list pairs is:

```text
1 + 4 + 16 + 64 + 256 = 341
```

Results:

```text
UNZIP(ZIP(xs,ys))                       341 / 341
UNZIP-SWAPPED(ZIP-SWAPPED(xs,ys))      341 / 341

ZIP orientation observable              310 cases
UNZIP orientation observable            310 cases

ZIP orientation involution              341 / 341
UNZIP orientation involution            341 / 341
```

Exactly 31 cases have `xs = ys`; the other 310 expose orientation.

Negative controls:

```text
swap ZIP only, keep normal UNZIP        310 roundtrip failures
normal ZIP, swap UNZIP only             310 roundtrip failures
```

So orientation must be changed coherently on both sides of the product law.

## Coordinate/gauge result

Current D6 authority:

```text
D6 ZIP   = 111000
D6 UNZIP = 111001
```

Candidate family:

```text
11100000
11100001
11100010
11100011
```

It has zero collision with the 64 selector research candidates.

With base/base anchored at ZIP-normal:

- `11100000 = ZIP` is a lower-domain duplicate;
- the middle `01/10` orbit contains lower-domain UNZIP and generated
  ZIP-SWAPPED;
- **`11100011 = UNZIP-SWAPPED`** is invariant under axis-order swap.

The square is typed: constructor and destructor have dual signatures, so
independence is proven through the commuting round-trip diagram, not by
pretending all four corners share one function type.

Status: **PRODUCT-CANDIDATE-TYPED**.

No D8 admission or callability follows from this witness.

## Reproduce

```sh
python3 benchmarks/d8-zip-unzip-orientation/run.py \
  --out /tmp/d8-zip-unzip-orientation
```
