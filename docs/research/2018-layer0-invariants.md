# Layer-0 invariants (#2018 / #1961)

**Agent:** grok-xai  
**Status:** research witnesses for **premises** — not theorems, not production reader  
**Checker:** `python3 scripts/research-2018-layer0-check.py`

## Why Layer-0

H-* packaging probes attack **bīja3 operator seeds**.  
Layer-0 sits **under** that table:

```text
Layer-0   D1 · racanā2 · explicit word boundaries
Layer-1   bīja3 operator seeds (premise)
Layer-2   local generators (CAR/CDR witness)
Layer-3   falsified geometries (Hamming, zero-pad EOS, …)
```

## Invariants checked

### D1 — predicate bits

```text
0 = NO
1 = YES
```

- Domain size exactly 2.  
- Structural `()` is **not** a D1 code (aligns H-NIL / PredicateBit: empty ≠ false bit).

### racanā2 — structure

```text
00  SEP     10  OPEN     01  CLOSE     11  DOT
```

- Exhausts width-2.  
- Disjoint from width-3 bīja3 codes (no accidental identity of `10` and `010`).

### Word boundaries

- Source = list of already-bounded words + widths.  
- Pack/unpack round-trip.  
- Internal `00` inside a width-3 seed does **not** split the word.  
- Zero-pad is **not** adopted as EOS (respects #1980 falsifier).

## Coordination

| lane | owner |
|------|--------|
| #2017 negative ledger | other agent (draft #2028) |
| H-* packaging | **closed** (grok-xai) |
| Layer-0 checker | **this** |
| production reader / #1971 wire | not here |

## One-line

```text
Bits for yes/no, bits for structure, cuts before packing — then seeds.
```
