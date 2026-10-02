# D7 Number-half map — #2443

Research snapshot from main `2e61d80a680284839ab69266de5d81217faac2c3`.

## Result

The current repository contains **no evidence that Core Number is a seven-bit semantic domain**.

The strongest current Number carrier is exact rational arithmetic:

```text
Q = arbitrary-precision numerator / denominator
```

implemented with `Rational` over arbitrary-precision `BigInt`. A particular integer may require 1, 7, 24, 128, or more bits, but that value-dependent bit length is not a semantic domain width.

The compact `Value::Number(f64, Exactness::Exact)` path is a storage/runtime optimization for exactly representable integers. Its 64 host bits are not Number identity.

Likewise:
- BigInt base-2^32 limbs are mechanism;
- FPGA limb widths are mechanism candidates;
- `NumericBuffer::I32/F32` are explicit fixed-width data formats;
- none of these proves D7 Number identity.

## Positive separation evidence

`Text7` does have an explicit logical width:

```text
Text7::LOGICAL_WIDTH = 7
```

and its source explicitly states that UPC-7 cells must not be interpreted as SENS Numbers. Its canonical wire tag `#t7:` is distinct from numeric/rational transport.

Exact-Q comparisons return **PredicateBit**, not Number. The exact-Q contract explicitly forbids Number 0/1 or 1/1 from becoming predicate identity.

## Core vs Core-Math

Core-Math #2433/#2437 provides mathematical donor evidence over exact Q, including generated NEG/SUB/DIV. It allocates no SENS bit coordinate and therefore supplies **no D7 Number width evidence**.

Any Core use of a Core-Math law still requires separate Core-domain evidence and ratification.

## Sound ↔ Number

No independently stated Sound↔Number semantic equation was found in the current evidence.

The current conservative D7 model therefore remains:

```text
Sound7  ⊎  Number-related Core research
```

or separate local grammars sharing a physical width in some representation — **not shared semantics**.

The panini falsifier reinforces the boundary: Text7 arithmetic/coercion is rejected. The observed `number->string(Text7)` behavior is a serializer type-boundary defect, not a Number coercion; it is isolated in #2446.

## Falsifier

The proposition

```text
"Number belongs to D7 because some Number values fit in 7 bits"
```

is false under current evidence.

Examples:

```text
0..127          may fit seven magnitude bits
2^100           does not
1/3             needs numerator + denominator structure
arbitrary Q     has no fixed seven-bit capacity
```

A domain width must belong to semantic identity, not to the accidental bit length of one value.

## Status

- Sound 7-bit coordinate: **evidenced on Sound/Text side, still D7 research**
- Number 7-bit semantic carrier: **NO WITNESS**
- Sound↔Number semantic law: **NO WITNESS**
- shared-bit representation: **insufficient for semantic identity**
- D7 admission: **none from this research slice**

See `number-map.tsv` for the machine-readable carrier table.
