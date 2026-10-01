# #2106 — Foundation−1: binary substrate before meaning

Status: research-only. No production or contract authority transfer.

## Result

The current layer-0 assumptions split into a weaker neutral carrier plus additional semantic orientations.

### Neutral carrier candidate

```text
alphabet cardinality = 2
word = finite ordered bit sequence
word boundary = explicit relation outside payload bits
meaning = absent until separately admitted
```

The project may continue to spell the two carrier symbols `0` and `1`, but the carrier itself does not attach NO/YES or structural meaning to those labels.

## 1. Global bit-flip symmetry

Across all words of widths 0..5, the witness checks 3969 word pairs.

Under global complement `0 <-> 1`, these neutral facts are preserved:
- width;
- equality/non-equality;
- prefix relation;
- concatenation.

Therefore the bare carrier does not distinguish an intrinsic orientation between its two symbols.

### Consequence for D1

`0=NO, 1=YES` may remain an admitted PredicateBit law, but it is **additional semantic orientation**, not a theorem of binary storage.

Swapping carrier symbols while keeping NO/YES labels fixed changes predicate meaning. Swapping both carrier symbols and polarity labels yields an isomorphic model.

## 2. racanā2 exact codes are not derived from role names alone

Abstract roles under test:

```text
sep, open, close, dot
```

Available 2-bit codewords:

```text
00, 01, 10, 11
```

All `4! = 24` bijections between roles and codewords encode/decode the same abstract role sequences correctly.

Therefore the current mapping:

```text
00 -> sep
10 -> open
01 -> close
11 -> dot
```

is not derived from the abstract four-role grammar alone.

This does **not** reject racanā2. It means the exact code assignment needs an independent law/evidence source if it is to become more than a premise.

## 3. Raw in-band delimiter impossibility

For every non-empty delimiter candidate of widths 1..8 (`510` candidates total), the delimiter itself is an admissible binary payload and also can occur strictly inside a larger payload.

Hence, if arbitrary finite binary words are allowed:

> no fixed unescaped bit pattern can safely serve as a universal word delimiter.

This is stronger than a coding preference. Under the stated assumptions, boundary needs framing, escaping, out-of-band structure, length information, or another mechanism external to raw payload scanning.

A structural word whose complete identity is `00` is therefore distinct from the substring `00` occurring inside a longer word.

## 4. Epsilon remains open

Two carrier models are internally consistent:

```text
{0,1}*   includes epsilon and has concatenation identity
{0,1}+   excludes epsilon
```

Both preserve the positive-word laws currently needed by Foundation-0.

Therefore `epsilon forbidden` is not derived from the neutral carrier.

#2077 has been weakened accordingly: epsilon can round-trip mechanically while semantic admission remains unresolved.

## Epistemic split proposed for #2018

```text
binary alphabet cardinality=2          premise / owner design choice
carrier 0<->1 symmetry                 witness
PredicateBit 0=NO,1=YES                semantic premise/witness, not carrier law
explicit boundary vs payload           theorem under arbitrary-word + no-escape assumptions
racanā2 abstract role inventory        premise
racanā2 exact code assignment          premise; not derived by role grammar
epsilon semantic admission             unknown
```

## Foundation stack after this result

```text
Foundation−1:
  neutral binary carrier + explicit boundaries

Foundation 0:
  exact bounded word identity

Foundation 1:
  semantic admission / evidence

Foundation 2:
  proof / relation laws

Foundation 3:
  execution mechanisms
```

## Principle

**The carrier supplies distinctions and order; semantics supplies orientation and meaning.**