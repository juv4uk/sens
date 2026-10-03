# Core-Math minimal binary executor — #2485

This experiment implements the canonical ontology of #2490:
```text
semantic object = binary number + declared domain + proved law
```

The semantic core is strictly smaller than the surrounding research stack:
- Semantic object: exact-width `BinaryNumber` qualified by `Domain` (`SelectorPath` or `QGroupFactor`).
- Canonical mechanism:
  ```text
  y = 2x + b
  width(y) = width(x) + 1
  b in {0,1}
  ```
- Domain firewall: cross-domain application fails closed with `DomainMismatch` (#2508, #2509).
- Reusable: generated binary objects in a domain feed directly into further law applications.
- Zero dependencies: no external crates, no Lisp, JSON, AST, hashes, registry rows, or caches required.

## Domains and Laws

### 1. `SelectorPath` (#2485, #2495)
- Roots: `101` (`Choice::First`), `110` (`Choice::Rest`).
- Semantic law: `extend(selector, b)(x) = selector(project_b(x))`.
- 252 bounded semantic witnesses through suffix depth 5.
- Slot permutation attack catches arbitrary swapping.

### 2. `QGroupFactor` (#2494, #2500)
- Roots: `0` (additive family), `1` (multiplicative family).
- Role bit: `0` (inverse), `1` (quotient).
- Children:
  - `00`: additive inverse (`NEG`)
  - `01`: additive quotient (`SUB`)
  - `10`: multiplicative inverse (`RECIP`, partial at 0)
  - `11`: multiplicative quotient (`DIV`, partial at y=0)
- 104 defined exact-Q cases and 8 undefined cases on 7-element corpus.
- Anti-numerology: 22/24 arbitrary width-2 permutations rejected by the factor law.

## Domain Firewall (#2508, #2509)

The binary factor-2 append mechanism is shared between `SelectorPath` and `QGroupFactor`, but:
- Cross-domain application (`apply(selector_law, q_object, delta)`) is rejected with `DomainMismatch`.
- Objects with identical bit strings in different domains (`10` Selector vs `10` QGroupFactor) remain distinct semantic objects.
- Erasing the domain tag loses semantic meaning (`AMBIGUOUS-WITHOUT-DOMAIN`).