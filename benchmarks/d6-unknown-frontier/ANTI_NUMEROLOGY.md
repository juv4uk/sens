# #2664 lane C — PURE-UNKNOWN symmetry

Status: research-only. No D6 resident is allocated.

The canonical D6 frontier already distinguishes:

- 16 generated selector residents;
- 44 `PURE-UNKNOWN` coordinates;
- `001100` as parent-duplicate/not-earned;
- `001101/001110` as nonadmitted middle product overlays;
- `001111` as owner-ready/nonadmitted.

This lane asks only whether the **printed bit patterns of the 44 PURE-UNKNOWN
rows** can supply a semantic preference before any new law is proved.

## Symmetry claim

Until a semantic theorem distinguishes two PURE-UNKNOWN rows, any transposition

```text
a <-> b
```

with `a,b` both PURE-UNKNOWN is an admissible anti-numerology relabeling,
provided every generated/distinguished D6 row is fixed.

The transpositions from one anchor to every other PURE-UNKNOWN coordinate show
that the 44 rows form one transitive symmetry orbit under this negative-control
model.

Therefore no unique resident can be justified by:

- smallest/largest numeric code;
- Hamming weight;
- Hamming distance to generated coordinates;
- distance to `001111`;
- longest prefix shared with D4 DEFINE;
- lexicographic order;
- any similar raw-bit aesthetic.

Such a ranking may still be a mechanism/layout heuristic later, but it is not
semantic placement evidence.

## What breaks the symmetry

A PURE-UNKNOWN coordinate may leave the orbit only when independent evidence
adds structure such as:

```text
same-base parent
+ independently witnessed deltas/generator
+ domain authority
+ executable witness
+ falsifier
+ collision/relabel attack
```

The law must come first; the coordinate is then a consequence.

## Non-conclusions

This witness does not prove that the 44 coordinates stay empty forever.
It does not rank future semantic laws.
It does not affect the `001111` owner decision.
It does not place non-local-exit or any historical operation.

## Reproduce

```sh
python3 benchmarks/d6-unknown-frontier/anti_numerology.py
```

Expected:

```text
D6-PURE-UNKNOWN-ANTI-NUMEROLOGY=PASS
PURE-UNKNOWN=44
SYMMETRY-ORBIT=44
TRANSITIVE=YES
COORDINATE-ONLY-CANDIDATE=REJECT
NEW-CANDIDATES=0
OCCUPANCY-MUTATIONS=0
```
