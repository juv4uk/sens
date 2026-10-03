# 2410 — Full Historical Occupancy of Domain 8 (D8)

**Status:** OWNER-DIRECTED METHOD, AGENT-DERIVED CONTENT. The D3→D6 occupancy rule was directed by the owner on 2026-10-03; the 192 historical coordinates allocated here are an agent-derived chronological continuation and are **not** an owner-ratified semantic allocation.

Українська версія: [2410-d8-historical-full-occupancy.uk.md](2410-d8-historical-full-occupancy.uk.md).

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
D4 coordinate plus one bit, every D6 coordinate is a D5 coordinate plus one bit,
and full occupancy is the ratified property (`unallocated = 0`).

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

## 2. Occupancy

| Quantity | Value |
|---|---|
| Width | 8 bits |
| Capacity | 256 |
| Occupied | 256 |
| Unallocated | 0 |
| Selector coordinates (law-generated) | 64 |
| Historical capability coordinates | 192 |
| Unique resident names | 256, zero collisions with D5/D6 |

Historical provenance distribution of the 192 derived rows:

| Lineage | Coordinates |
|---|---:|
| Common Lisp | 117 |
| Lisp 1.5 (outside the selector family) | 53 |
| MacLisp | 22 |
| Lisp Machine | 4 |
| McCarthy 1960 | 3 |
| Scheme | 1 |
| Functional Lisp tradition | 1 |

Status counts by category:

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

## 4. The historical half is a derived continuation

The remaining 192 coordinates receive four chronological historical capabilities
per D6 parent, each one an extension of that parent, in historical order. Worked
example — `100000` `NCONC` (destructive list concatenation):

| Coordinate | D6 parent | Resident | Family | Origin |
|---|---|---|---|---|
| `10000000` | `100000` NCONC | `COPY-LIST` | list-structure | Lisp 1.5 |
| `10000001` | `100000` NCONC | `REVAPPEND` | list-structure | Lisp 1.5 |
| `10000010` | `100000` NCONC | `LIST*` | list-structure | Common Lisp |
| `10000011` | `100000` NCONC | `LIST-LENGTH` | list-structure | Lisp 1.5 |

Full table: the `coordinates` array of the JSON map, one row per coordinate with
`name`, `category`, `behavior`, `provenance`, `evidence`, `parent_d6`,
`parent_d7`, `lineage_parent_name`.

## 5. Epistemic status — what this document does NOT establish

- **The 192 rows are agent-derived.** No single historical source attests this
  particular coordinate assignment. `provenance` names the dialect lineage each
  capability comes from; it is not a page citation.
- **Occupancy is not irreducibility.** A coordinate can be filled and still be
  derivable from a smaller law basis. That axis is tracked separately (#2765).
- **This map is not language authority.** `language-contract.lisp` remains the
  machine-readable contract. A coordinate here is an occupancy claim under the
  D3→D6 rule, not a ratified semantic identity.
- **D7 was not reinterpreted.** This document crosses the D7 rung on the strength
  of `d7-full-map.json`'s own `occupancy_rule`; it does not weaken, re-admit or
  re-describe any Text7/Sound7 cell, and the 21 reserved Text7 cells remain
  untouchable (#2494).
- **No Rust carrier was added.** D5 and D6 have typed Rust carriers neither, so
  adding one only for D8 would create an asymmetric mechanism commitment. The
  mechanical `Bit8` / `BinarySourceWord::W8` already exist and are untouched.

## 6. Reproducibility and gates

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
D8 width=8 capacity=256 occupied=256 unknown=0
parent_d6 = full D6 map, exactly 4 children per D6 parent
parent_d7 = one-bit prefix, exactly 2 children per D7 prefix
64/64 selector coordinates equal the generator law
D8 selector word set == #2322 forecast word set (independent witness)
256 unique resident names, no collision with D5/D6
every row carries behaviour, provenance and evidence class
d7-full-map.json still documents that D7 is not a one-bit extension
```

If `d7-full-map.json` ever stops documenting that D7 is outside the D5/D6 rung,
the guard fails on purpose: the D8 lineage decision would have to be revisited.