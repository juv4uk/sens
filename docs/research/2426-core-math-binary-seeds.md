# #2426 — Core-Math Minimal Binary Seeds and Laws

Status: P0 research implementation.
Parent ontology: #2490.
Growth foundation: #2460 / PR #2636.
Executor foundation: #2485 / PR #2623.
Domain firewall: #2508 / #2509.
Convergence: #2495.

## Result

The minimal basis remove-one necessity tournament is implemented in Rust with zero external dependencies in `benchmarks/core-math-binary-seeds/`.

The research answers the foundational question of #2426:
```text
Every binary seed must earn the right to exist.
```

### 1. Remove-One Tournament Methodology
For each candidate premise in a basis $\mathcal{B} = (\mathcal{S}, \mathcal{L})$:
- The system generates the bounded capability closure $\mathcal{C}(\mathcal{B})$.
- The candidate premise $p$ is removed, and the reduced closure $\mathcal{C}(\mathcal{B} \setminus \{p\})$ is computed.
- The capability delta $\Delta\mathcal{C} = \mathcal{C}(\mathcal{B}) \setminus \mathcal{C}(\mathcal{B} \setminus \{p\})$ determines necessity:
  - If $\Delta\mathcal{C} \neq \emptyset$: premise $p$ is **strictly necessary**.
  - If $\Delta\mathcal{C} = \emptyset$: premise $p$ is **redundant** and rejected from the minimal basis.

### 2. Canonical Minimal Basis (11/11 strictly necessary)
The evaluated canonical basis contains 6 seeds and 5 laws:
- **`Domain::QGroupFactor` (#2494)**:
  - Seed `0` (additive root): removal loses NEG (`00`) and SUB (`01`).
  - Seed `1` (multiplicative root): removal loses RECIP (`10`) and DIV (`11`).
  - Law `inverse_role` (delta `0`): removal collapses inverse generation.
  - Law `quotient_role` (delta `1`): removal collapses quotient generation.
- **`Domain::SelectorPath` (#2485, #2495)**:
  - Seed `101` (First root): removal collapses CAR-rooted paths.
  - Seed `110` (Rest root): removal collapses CDR-rooted paths.
  - Law `extend_zero` (delta `0`): removal collapses First projections.
  - Law `extend_one` (delta `1`): removal collapses Rest projections.
- **`Domain::AffineFunctionGF2` (#2319)**:
  - Seed `100111` (Inversion): removal collapses NOT and odd-parity composite transforms.
  - Seed `011000` (Swap): removal collapses coordinate transposition.
  - Law `composition`: removal collapses all composite function construction.

### 3. Identity Seed Theorem
A key mathematical outcome of the tournament:
In $\mathrm{AGL}(2,2)$, the Identity element (`100100`) is derived from the square of any involution:
$$\mathrm{Inversion} \circ \mathrm{Inversion} = \mathrm{Identity}$$
$$\mathrm{Swap} \circ \mathrm{Swap} = \mathrm{Identity}$$
Consequently, retaining Identity as an axiomatic seed in a basis with Inversion or Swap is **redundant**. Identity earns its existence as a theorem, shrinking the axiomatic seed count.

### 4. Redundancy Falsifiers
The benchmark executes two explicit negative controls:
1. **Derivable Child Seed**: Inversion of child `1010` into the basis fails the remove-one test ($\Delta\mathcal{C} = \emptyset$) $\implies$ correctly flagged as redundant.
2. **Identity Coordinate**: Insertion of `100100` into the basis fails the remove-one test ($\Delta\mathcal{C} = \emptyset$) $\implies$ correctly flagged as redundant.

### 5. Architectural Invariants
- Zero external crate dependencies (`[dependencies]` is strictly absent in `Cargo.toml`).
- Execution requires no Lisp runtime, JSON, AST, SHA hashes, or registries.
