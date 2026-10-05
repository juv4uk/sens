# D8 ANY/ALL × predicate polarity — #3663

This is a research-only D8 product witness. It does not admit a D8 resident or
change runtime callability.

## Current inputs

- D6 ANY/ALL law: #3370;
- D6 owner-ratified coordinate authority: #3393;
- D8 remains research: #3281 / Contract 11.6;
- clean product-screen parent: #3651.

No historical D8 donor is used to derive the law.

## Two semantic axes

The current D6 pair gives the first axis:

```text
quantifier = ANY | ALL
```

The existing De Morgan law gives a candidate independent second axis:

```text
predicate polarity = p | NOT∘p
```

So the semantic square is:

```text
                 p              NOT∘p
ANY              ANY            ANY-NOT
ALL              ALL            ALL-NOT
```

## Exhaustive finite witness

The test universe is intentionally complete for the chosen finite carrier:

- alphabet `{0,1}`;
- **all 4 predicates** over that alphabet;
- all 63 lists of lengths 0..5.

Total: **252 cases**.

Results:

```text
ALL(NOT p) = NOT ANY(p)       252 / 252
ANY(NOT p) = NOT ALL(p)       252 / 252

ANY vs ALL at p                108 differing cases
ANY vs ALL at NOT p            108 differing cases
p vs NOT p under ANY           144 differing cases
p vs NOT p under ALL           144 differing cases
```

All four functionals are globally pairwise distinct. Their full truth-table
distances are:

```text
ANY(p)      vs ALL(p)          108 / 252
ANY(p)      vs ANY(NOT p)      144 / 252
ANY(p)      vs ALL(NOT p)      252 / 252
ALL(p)      vs ANY(NOT p)      252 / 252
ALL(p)      vs ALL(NOT p)      144 / 252
ANY(NOT p)  vs ALL(NOT p)      108 / 252
```

## Uniqueness falsifier

There are only `4! = 24` permutations of the four predicate truth tables.

The witness exhausts all 24 and asks which predicate transform satisfies **both**
De Morgan equations on all 252 cases.

Result:

```text
predicate transforms tested     24
transforms that pass both laws   1
```

The unique survivor is pointwise predicate complement.

So the polarity axis is not selected from an aesthetic bit symmetry; it is
uniquely fixed by the semantic laws in this finite universe.

## Coordinate/gauge result

Current D6 authority resolves:

```text
D6 ANY = 111100
D6 ALL = 111101
```

Candidate D8 family:

```text
11110000
11110001
11110010
11110011
```

This family has zero collision with the 64 selector research candidates.

Anchoring base/base at `ANY(p)` fixes:

```text
11110000 = ANY(p)
```

as a lower-domain duplicate.

Swapping axis order exchanges only the two middle corners. Therefore:

- `ALL(p)` is the lower-domain duplicate in the middle orbit;
- `ANY(NOT p)` is a generated novel semantic candidate, but its absolute
  middle coordinate is still gauge-unfixed;
- **`11110011 = ALL(NOT p)`** is invariant under axis-order swap.

These are generated semantic candidates. The witness does **not** claim that
they should become primitive D8 residents.

## Reproduce

```sh
python3 benchmarks/d8-any-all-polarity/run.py \
  --out /tmp/d8-any-all-polarity
```
