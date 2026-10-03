# #2485 — Domain-Scoped Minimal Binary Executor

Status: P0 research implementation.
Parent ontology: #2490.
Domain firewall: #2508 / #2509.
Exact-Q donor: #2494 / PR #2500.
Selector convergence: #2495 / PR #2585.

## Result

The minimal Core-Math binary executor (`benchmarks/core-math-binary-exec/`) is upgraded from a flat `(bits, factor) -> bits` arithmetic helper to the full #2490 canonical ontology:

```text
semantic object = binary number + declared domain + proved law
```

### 1. Declared Domains

The executor explicitly types every semantic object and law under:
- `Domain::SelectorPath`: variable exact-width selector paths rooted at Core D3 `101` (First) and `110` (Rest).
- `Domain::QGroupFactor`: exact-Q group-factor coordinates rooted at `0` (additive family) and `1` (multiplicative family).

### 2. Domain-Scoped Execution

The semantic operation:
```rust
apply(law: &Law, parent: &SemanticObject, delta: &BinaryNumber) -> Result<SemanticObject, Error>
```
enforces:
1. `parent.domain() == law.domain()`, failing closed with `Error::DomainMismatch` on any cross-domain application.
2. `delta.width() == 1`, enforcing single-bit coordinate extension.
3. `law.factor() == 10₂`, computing `child = 2 * parent + delta` with `width = parent_width + 1`.

### 3. Integrated Donor Laws

#### SelectorPath (#2485, #2495)
- Law: `extend(selector, b)(x) = selector(project_b(x))`.
- 252 bounded semantic witnesses through suffix depth 5.
- Unbounded bit carrier: tested with 4096-bit input yielding 4097-bit output.
- Slot permutation attack catches arbitrary child swapping.

#### QGroupFactor (#2494, #2500)
- Roots: `0` (additive family), `1` (multiplicative family).
- Role bit: `0` (inverse), `1` (quotient).
- Children: `00` (NEG), `01` (SUB), `10` (RECIP, partial at 0), `11` (DIV, partial at y=0).
- 104 defined exact-Q cases + 8 undefined cases across a 7-element corpus.
- Anti-numerology: 22 out of 24 arbitrary permutations of the 4 child slots break the factor coordinate law, proving canonical factor structure.

### 4. Domain Firewall (#2508, #2509)

The identical bit mechanism `y = 2x + b` is shared between `SelectorPath` and `QGroupFactor`, but:
- `apply(selector_law, q_object, delta)` -> `Err(DomainMismatch)`.
- `apply(q_law, selector_object, delta)` -> `Err(DomainMismatch)`.
- Semantic objects with identical bits (`10` SelectorPath vs `10` QGroupFactor) are non-equal: `sel_10 != q_10`.
- Erasing domain produces `AMBIGUOUS-WITHOUT-DOMAIN`.

### 5. Architectural Invariants

- Zero external crate dependencies (`[dependencies]` is forbidden in `Cargo.toml`).
- Execution requires no Lisp runtime, JSON, AST, SHA hashes, registry rows, or caches.
- Generated binary objects are immediately reusable as input to further law applications within the same domain.
