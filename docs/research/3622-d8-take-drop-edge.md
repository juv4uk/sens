# D8 TAKE/DROP × edge product witness — #3622

This is a research-only D8 law experiment. It does not admit a D8 resident and
does not add a runtime mechanism.

## Inputs

Current semantic evidence only:

- D6 TAKE/DROP partition law — #3368;
- D5 REVERSE / REVERSE-ONTO local algebra — #3305 / #3293 / #3379;
- D6 coordinate authority — #3393;
- D8 remains research — #3281 / Contract 11.6.

No D7 ancestry and no historical D8 donor are used to derive the square.

## Candidate law

Use two independently observable binary choices:

```text
mode = take | drop
edge = left | right
```

with right-oriented forms defined by REVERSE conjugation:

```text
take_right(n,xs) = reverse(take_left(n, reverse(xs)))
drop_right(n,xs) = reverse(drop_left(n, reverse(xs)))
```

This gives the semantic square:

```text
                left          right
take            TAKE          take_right
drop            DROP          drop_right
```

## Bounded exhaustive witness

The executable witness enumerates every list over the alphabet `{0,1}` with
length 0..5 and every `n` from 0 through `length+2`.

Total: **447 deterministic cases**.

Current result:

```text
reverse involution           447 / 447
left partition               447 / 447
right partition              447 / 447

edge observable, take fixed  144 cases
edge observable, drop fixed  144 cases
mode observable, left fixed  438 cases
mode observable, right fixed 438 cases

four functions globally pairwise distinct  PASS
axis-order commutativity                 PASS
```

Negative controls:

```text
omit final reverse: partition fails      300 / 447
wrong right-drop = suffix: fails         438 / 447
```

The edge axis is therefore not a decorative relabel.

## Coordinate gauge

Anchor the research product on current D6 TAKE coordinate:

```text
D6 TAKE = 110000
D6 DROP = 110001
```

The candidate D8 coordinate family is:

```text
11000000
11000001
11000010
11000011
```

It has zero collision with the 64 selector candidates from #3615.

Parent preservation fixes:

```text
11000000 = TAKE-left
```

which is a lower-domain duplicate and earns no new D8 resident.

Swapping the two semantic axes swaps only the middle corners:

```text
mode,edge order:  01 take-right   10 DROP-left
edge,mode order:  01 DROP-left    10 take-right
```

Therefore the middle coordinate of `take_right` is still gauge-free between
`11000001` and `11000010`.

But the strongest corner is invariant:

```text
11000011 = drop_right
```

under either axis order.

So this experiment produces:

- one **orientation-invariant novel coordinate candidate**: `11000011`;
- one **novel semantic candidate with unresolved middle-coordinate gauge**:
  `take_right`;
- two lower-domain duplicates: TAKE-left and DROP-left.

This remains research. Owner ratification and a coordinate-orientation theorem
are separate gates.

## Reproduce

```sh
python3 scripts/research-3622-d8-take-drop-edge.py \
  --out /tmp/d8-take-drop-edge
```

The workflow runs the witness twice and byte-compares the JSON output.

## Authority freshness

The executable witness does not trust hardcoded D6 TAKE/DROP coordinates. It reads
`knowledge/d6-ratified.json`, requires owner authority `#3393`, resolves TAKE and
DROP from that current 64-row map, and writes the source-file SHA-256 into the
machine-readable artifact. Any future D6 authority movement therefore makes the
witness fail or changes its recorded provenance instead of silently preserving a
stale coordinate.
