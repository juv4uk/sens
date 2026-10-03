# 2410 — D8 admitted cells and attested candidates

**Status:** RATIFIED WIDTH/ONTOLOGY, AGENT-DERIVED CONTENT. #2410 ratifies the D8
domain width and ontology. It does not ratify occupancy. Following the #2415
precedent, this map admits **only** the 64 coordinates that an admitted law
generates, and keeps the other 192 as attested-but-unadmitted candidates whose
provenance is preserved as witness material.

The earlier version of this document claimed 256/256 occupancy with
`unallocated = 0`. **That claim is withdrawn** — see §4.

Українська версія: [2410-d8-admitted-cells-and-candidates.uk.md](2410-d8-admitted-cells-and-candidates.uk.md).

**Machine-readable map:** [`knowledge/d8-historical-full-map.json`](../../knowledge/d8-historical-full-map.json)
**Builder:** [`scripts/build-d8-historical-full-map.py`](../../scripts/build-d8-historical-full-map.py)
**Guard:** [`scripts/check-d8-full-map.py`](../../scripts/check-d8-full-map.py)

```text
python3 scripts/build-d8-historical-full-map.py
python3 scripts/check-d8-full-map.py
```

---

## 1. Why D8 and not D7

The D5/D6 occupancy rule is a **one-bit extension rule**: every D5 coordinate is a
D4 coordinate plus one bit and every D6 coordinate is a D5 coordinate plus one bit.
This document originally treated "full occupancy is the ratified property
(`unallocated = 0`)" as carrying over to D8. It does not. #2415 states the
boundary for the ratified 7-bit domain:

> Ratification covers the domain width/ontology and semantic role, not blanket
> occupancy of all 128 coordinates.

D8 is governed by the same boundary: the ratified part is width, ontology and
lineage, not 256/256 occupancy.

D7 is not a rung of that ladder, and the repository already says so in machine
form. [`knowledge/d7-full-map.json`](../../knowledge/d7-full-map.json):

```text
occupancy_rule: "class = the top 2 bits; payload = the low 5 bits.
 Unlike D5/D6, D7 is NOT a one-bit extension of a parent domain: a sound cell is
 not the P0/P1 child of another sound cell, so the D5/D6 occupancy rule does not
 transfer. D7 needs its own rule: a cell is admitted only with an exact 7-bit
 object + a D7 law/relation + a witness."
authority: "derived-research-not-owner-directive"
```

D7 therefore owns the Text7/Sound7 articulatory law (`sthāna` × `prayatna`, plus
convention signs) and is not a historical-capability rung. Under the
constitutional principle of #2497 (*a domain owns the law it operates*; recorded in
`docs/research/2497-d7-d14-constitutional-demarcation.md` on the D7/OD-008 line of
work, not on this branch) —
*a domain owns the law it operates* — a 7-bit sound cell cannot be re-used as the
parent of 8-bit historical capability coordinates.

So the historical ladder D1→D6 continues at the next free width, D8, and it does
so as a **two-bit extension**:

```text
D4 --+1 bit--> D5 --+1 bit--> D6 --+2 bits--> D8
                                  |
                                  +-- D7 crossed: different law (Text7/Sound7)
```

Every D8 coordinate therefore records two different things:

| Field | Meaning | Checked as |
|---|---|---|
| `parent_d6` | lineage parent: the 6-bit historical coordinate it extends | `coordinate[:-2]`, 4 children per D6 parent, parent set == full D6 map |
| `parent_d7` | mechanical one-bit prefix: the 7-bit word that exists | `coordinate[:-1]`, 2 children per D7 prefix, 128 prefixes |

Width is part of identity (`1 != 01 != 001`), so a 7-bit sound cell and its 8-bit
D8 children are **different identities**. Recording both fields keeps the lineage
honest without importing the D7 law.

## 2. Admission, not occupancy

| Quantity | Value |
|---|---|
| Width | 8 bits |
| Capacity | 256 |
| **Admitted by law** | **64** |
| **Attested but not admitted** | **192** |
| Blanket occupancy claim | **withdrawn** |
| Admitted selector coordinates (law-generated) | 64 |
| Unique names across all 256 | 256, zero collisions with D5/D6 |

Provenance distribution of the 192 **candidates** (witness material, not
occupancy):

| Lineage | Coordinates |
|---|---:|
| Common Lisp | 117 |
| Lisp 1.5 (outside the selector family) | 53 |
| MacLisp | 22 |
| Lisp Machine | 4 |
| McCarthy 1960 | 3 |
| Scheme | 1 |
| Functional Lisp tradition | 1 |

Status counts by category across all 256 rows:

```text
selector 64 · predicate 18 · control 19 · arithmetic 17 · numeric-conversion 14
bit-operation 13 · binding 11 · higher-order 11 · physical-mutation 11
sequence 10 · abstraction 8 · list-structure 8 · lookup 8 · macro 8
special-form 8 · system 8 · set-operation 7 · generalized-place 5
state 4 · stream 4
```

## 3. The selector half is generated, not allocated

All 64 selector coordinates come from the already admitted D3 law:

```text
roots:        101 = CAR, 110 = CDR
append 0  =>  compose CAR
append 1  =>  compose CDR
name       =>  C + letters + R
```

D8 selector words are `root + 5 suffix bits`, giving `2 × 2⁵ = 64` coordinates.
The 16 D6 selector parents each have exactly four selector children, so the
selector sub-lattice reproduces itself mechanically:

```text
D6  101000 = CAAAAR
D8  10100000 = CAAAAAAR    10100001 = CAAAAADR
    10100010 = CAAAADAR    10100011 = CAAAADDR
```

Two independent witnesses agree on the word set:

1. the guard recomputes every name from the law and requires an exact match;
2. the guard imports `scripts/research-2322-generative-domain-forecast.py` and
   requires set equality with `selector_words(8)`.

The forecast is research-only accounting, so it is used as a second witness and
never as an allocation authority.

## 4. The historical half: a rule that was falsified, not a law

The 192 non-selector coordinates were previously assigned by this rule:

> four chronological historical Lisp capabilities per D6 parent

The factor-analysis that #2506 passes for D6 — *do four children decompose into
two independent one-bit refinements whose commutation is witnessed?* — **fails
here**:

| D6 parent | Its four candidates | Factors into commuting bits? |
|---|---|---|
| `000001` LOAD | OPEN, CLOSE, WITH-OPEN-FILE, DRIBBLE | **no** — OPEN and CLOSE are two poles of one operation, not two instances of one refinement |
| `000101` LEXPR | ARGLIST, &REST, &OPTIONAL, &WHOLE | **axes commute, assigned names are not the corners** — see below |
| `000010` CLOSURE | MAKE-CLOSURE, CLOSUREP, VALUES, VALUES-LIST | **no** — two unrelated pairs |
| `000011` CURRY | APPLY, COMPOSE, PARTIAL, **FFI-CALL** | **no** — a foreign-function call is not a curry descendant |

The last row is a category error produced by the rule itself, which is a
sufficient falsifier.

### LEXPR is the instructive case: a real square that is not the assigned one

`&REST` × `&OPTIONAL` is a genuine pair of commuting bits — a lambda list may
independently declare a trailing rest parameter, optional leading parameters,
both, or neither. That square is real, and it commutes.

It is still not the square the rule assigned, and the executable witness
`scripts/research-2934-d8-lexpr-factoring.py` proves where it breaks:

```text
00 = neither                 -> ARGLIST          (accepted: plain variadic eval)
01 = optional only           -> &OPTIONAL        (accepted)
10 = rest only               -> &REST            (accepted)
11 = both                    -> &REST+&OPTIONAL  (assigned &WHOLE instead)
```

Two independent falsifiers:

- the `11` corner of the real axis square is `&REST+&OPTIONAL`, which is not
  `&WHOLE` — the witness checks they have different observation signatures;
- the `00` corner must be the parent `LEXPR` itself, and `ARGLIST` is a distinct
  accessor of the argument list rather than a parameterless `LEXPR`.

Recorded distinction: the falsifier is *not* "these two names are alternatives,
therefore they do not commute". Parallel independent choices are exactly what
commuting bits look like. The falsifier is that the four assigned names are not
the corners of the square the axes actually generate.

ADR-005 §4 (owner directive) requires a primitive to earn a semantic identity
through an **executable experiment**. A chronological capability list is neither a
law nor an experiment. So the 192 coordinates are demoted to
`attested-not-admitted`: their `provenance`, `behavior` and `admission_reason`
are preserved so the witness material is not lost, but they are not counted as
occupancy and they do not sit in `coordinates`.

They live in `unassigned_candidates` in the JSON map.

### How D8 will actually be filled

One admitted law at a time. For each of the **48** remaining non-selector D6
parents, D8 needs two independent one-bit refinements of that parent plus an
executable witness that the two commute — exactly the shape #2506 used for D6.
Only then do historical Lisp functions enter as **positive controls** rather than
allocations.

The progress metric is the count of independent admitted laws that earned
inhabitants, **not** occupancy out of 256.

### Executed factoring tests, including the strongest candidates

Verbal judgment is not evidence, so three parents have executable witnesses. Two
were chosen because they are the *most likely* to pass, not the least.

| Parent | Witness | Verdict |
|---|---|---|
| `010010` INTEGERP | `research-2934-d8-integerp-factoring.py` | refuted |
| `001101` WHILE | `research-2934-d8-while-factoring.py` | refuted |
| `000101` LEXPR | `research-2934-d8-lexpr-factoring.py` | refuted |

`FLOOR/CEILING/TRUNCATE/ROUND` is the canonical illusion of a 2×2 product: two
rounding "axes" that look orthogonal. The decisive test is that neither
refinement is **injective**. Setting one bit of a real 2×2 product always yields
four distinct results; here `toward_zero` maps the four corners onto only two:

```text
toward-zero refinement image : [(True, False), (True, True)]   # 2 of 4
toward-+inf refinement image : [(False, True), (True, True)]  # 2 of 4
```

So these are projections that forget which corner they started from — two
encodings of one decision ("where does the remainder go"), not two bits.

`WHILE` is a genuinely orthogonal pair of axes, and that is exactly why it fails:
`{loop-form, predicate} × {positive, negative}` generates four corners, and two
candidates compete for one of them.

```text
(False, False) -> ALWAYS      (predicate, positive)
(False, True)  -> NEVER       (predicate, negative)
(True,  False) -> WHILE       (loop form, positive)
(True,  True)  -> UNTIL       (loop form, negative)
EVERY also wants (False, False), and differs observationally from ALWAYS
```

Four slots, five names, no forced assignment. The axes are real; the *names* are
not the corners.

Recorded honesty note: an early version of the WHILE witness reported `ALWAYS`
and `EVERY` as identical, which would have been a stronger-looking refutation.
It was a defect in a deliberately coarse test model, not a finding — in Common
Lisp `EVERY` returns the last element's value while `ALWAYS` returns `T`. The
model was corrected before any verdict was recorded.

## 5. Non-conflation: D8 is not a byte table

D8 is an exact 8-bit Core domain. Legacy Sens8 is an 8-bit flat table in which
the byte is simultaneously address and identity. Equal width does not imply
shared type or shared law.

The precedent is #2415 again: Sound7 cells and local `śloka`/`sūtra` ordinals
both use seven-bit values without implying one arithmetic Number type or law.

This was also checked rather than assumed. **8** of the 183 legacy Sens8 EN
surface names reappear in this map, and **not one of the eight shares a
coordinate** with its legacy byte:

| Name | legacy Sens8 byte | D8 coordinate |
|---|---|---|
| `APPLY` | `10101111` | `00001100` |
| `MAP` | `00110111` | `11110001` |
| `MOD` | `00010011` | `01000011` |
| `READ` | `01001010` | `00000000` |
| `PRINT` | `01001000` | `00000001` |
| `PRINC` | `01001001` | `11111001` |
| `REDUCE` | `00111001` | `01110110` |
| `SQRT` | `00010101` | `01010100` |

So D8 is not a relabelled byte table — a suspicion that was held and then
disproved by measurement.

## 6. Epistemic status — what this document does NOT establish

- **The 192 candidates are not identities.** They are historical witnesses kept
  visible so the material is not lost. `provenance` names a dialect lineage, not
  a page citation, and no admitted law generates those coordinates.
- **Blanket occupancy is not claimed.** 256/256 and `unallocated = 0` were
  withdrawn; the guard now fails if they are reinstated.
- **Occupancy is not irreducibility.** A coordinate can be admitted and still be
  derivable from a smaller law basis. That axis is tracked separately (#2765).
- **This map is not language authority.** `language-contract.lisp` remains the
  machine-readable contract. A coordinate here is an admission under an admitted
  law, not a ratified semantic identity.
- **D7 was not reinterpreted.** This document crosses the D7 rung on the strength
  of `d7-full-map.json`'s own `occupancy_rule`; it does not weaken, re-admit or
  re-describe any Text7/Sound7 cell, and the 21 reserved Text7 cells remain
  untouchable (#2494).
- **No Rust carrier was added.** D5 and D6 have typed Rust carriers neither, so
  adding one only for D8 would create an asymmetric mechanism commitment. The
  mechanical `Bit8` / `BinarySourceWord::W8` already exist and are untouched.

## 7. Reproducibility and gates

The map is generated, not hand-maintained. CI re-runs the builder and requires a
clean diff, so the committed JSON cannot drift from the D6 map or from the
builder:

```text
.github/workflows/d8-full-map.yml
  → python3 scripts/check-d8-full-map.py
  → python3 scripts/build-d8-historical-full-map.py
  → git diff --exit-code -- knowledge/d8-historical-full-map.json
```

Guard invariants, all currently passing:

```text
D8 width=8 capacity=256
D8 admitted=64 (every one of them by the admitted D3 CAR/CDR selector law)
D8 attested-not-admitted=192 (provenance preserved as witness material)
D8 blanket-occupancy claim: WITHDRAWN (see #2415 ratification scope)
parent_d6 = full D6 map, exactly 4 children per D6 parent
parent_d7 = one-bit prefix, exactly 2 children per D7 prefix
64/64 selector coordinates equal the generator law
D8 selector word set == #2322 forecast word set (independent witness)
256 unique names, no collision with D5/D6
every row carries behaviour, provenance and evidence class
d7-full-map.json still documents that D7 is not a one-bit extension
```

The guard is load-bearing in both directions. Each of these mutations fails:

| Mutation | Guard response |
|---|---|
| mark a candidate `admitted-by-law` | `candidate must not be marked admitted` |
| delete `falsified_rules` | `must keep the falsified historical rule on record` |
| restore blanket occupancy | `D8 admitted count drift` |
| delete `non_conflation` | `must record the 8-bit non-conflation rule` |

If `d7-full-map.json` ever stops documenting that D7 is outside the D5/D6 rung,
the guard fails on purpose: the D8 lineage decision would have to be revisited.