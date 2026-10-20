# Scientific constants as Lisp data

> **Status:** current design, defining-SI slice confirmed on 2026-09-07.  
> **Evidence:** `crates/my-lisp/tests/scientific_constants.rs`, CI #1069.  
> **Scope:** representation and Advice Taker admission. Unit algebra is not claimed.

## Principle

A bare number, a physical quantity, and a scientific constant are different
semantic objects:

```text
299792458
    ≠
299792458 m/s
    ≠
"the SI defining value of the speed of light is exactly 299792458 m/s"
```

`my-lisp` therefore does **not** add a `const` evaluator primitive. Scientific
meaning is represented by ordinary finite Lisp data in `lib/quantity.lisp`, and
SI data is expressed by `lib/si.lisp`.

## Versioned data shapes

```lisp
(dimension/1 BASE EXPONENT)

(unit/1
  (dimension/1 BASE EXPONENT)
  ...)

(quantity/1 VALUE UNIT)

(science-source/1 AUTHORITY EDITION)

(scientific-constant/1
  NAME
  QUANTITY
  STATUS
  KIND
  SYSTEM
  SOURCE)
```

Each nested semantic object has an atomic tag. In particular, units use named
`dimension/1` terms rather than anonymous pairs. This lets the same finite data
pass through the existing Advice Taker knowledge grammar without weakening its
validator.

## Epistemic vocabulary

The library recognizes these status names:

```text
exact-by-definition
exact-derived
measured
```

and these kinds:

```text
physical-defining
physical-derived
physical-measured
mathematical
```

Only the `exact-by-definition` + `physical-defining` SI slice is confirmed by
the current corpus. `exact-derived`, `physical-derived`, `measured`,
`physical-measured`, and `mathematical` are reserved vocabulary for later
experiments; their presence is not evidence that those cases are complete.

## The seven SI defining constants

`lib/si.lisp` stores one authoritative finite-data record for each defining
constant through its full Ukrainian `сі:визначальна-*` surface:

```text
si:defining-cesium-frequency
si:defining-speed-of-light
si:defining-planck-constant
si:defining-elementary-charge
si:defining-boltzmann-constant
si:defining-avogadro-constant
si:defining-luminous-efficacy
```

For example:

```lisp
(scientific-constant/1 si:speed-of-light
  (quantity/1 299792458
    (unit/1
      (dimension/1 metre 1)
      (dimension/1 second -1)))
  exact-by-definition
  physical-defining
  si
  (science-source/1 bipm-si-brochure-9 2019))
```

The established arithmetic bindings remain compatible:

```lisp
si:speed-of-light
si:planck-constant
...
```

but they are now derived from the corresponding records through
`сі:значення-константи`. The source does not repeat a second literal numeric
binding for those public names. This is the single-authority claim proved by
the regression test.

This does **not** make normal `def` bindings immutable. Same-frame rebinding is
still part of the language. The claim is narrower: the library has one
canonical data source for each defining value instead of two hardcoded copies.

## Exactness

All seven SI defining values remain exact integers or exact rationals. The
migration introduced no floating-point approximation. Existing exact-value
tests continue to pass.

`exact-by-definition` describes the epistemic status of these SI defining
records. It must not be reused for a quantity that is merely exactly derivable
from defining constants. `lib/si-derived.lisp` is therefore a separate future
migration slice; a derived constant needs derivation/provenance evidence, not a
false `exact-by-definition` label.

## Advice Taker boundary

`scientific-constant->clauses` is a pure projection. A valid record can produce
facts such as:

```lisp
(scientific-constant si:speed-of-light)
(constant-value si:speed-of-light 299792458)
(constant-unit si:speed-of-light
  (unit/1
    (dimension/1 metre 1)
    (dimension/1 second -1)))
(constant-status si:speed-of-light exact-by-definition)
(constant-kind si:speed-of-light physical-defining)
(constant-system si:speed-of-light si)
(constant-source si:speed-of-light
  (science-source/1 bipm-si-brochure-9 2019))
```

Projection itself never modifies `*knowledge-journal*`. The returned batch must
still cross the ordinary explicit admission boundary:

```text
scientific-constant/1
        ↓
scientific-constant->clauses     pure
        ↓
advise-all                       guarded write
        ↓
knowledge
        ↓
reason-in-observe
```

The current adversarial test proves that the projection is valid and pure,
that `advise-all` accepts the speed-of-light record, and that Advice Taker can
then prove its value, status, and structured unit.

## Explicit non-claims

The confirmed slice does **not** claim:

- a new `const` primitive;
- immutable variable bindings;
- numeric type checking inside every generic `quantity/1` value;
- full dimensional arithmetic or automatic unit normalization;
- dimensional compatibility checking for `+`, `-`, `*`, or `/`;
- measured-value uncertainty/epoch semantics;
- complete mathematical-constant representation;
- structured provenance for derived SI constants.

Those are separate hypotheses. They should be added only with executable
counterexamples and evidence, not inferred from the existence of the data
shapes above.
