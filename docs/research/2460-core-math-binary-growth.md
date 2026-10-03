# #2460 — Core-Math Autonomous Binary Growth and Demand Derivation

Status: P0 research implementation.
Parent ontology: #2490.
Executor foundation: #2485 / PR #2623.
Domain firewall: #2508 / #2509.
Minimal seeds: #2426.
Laws: #2425.

## Result

Autonomous binary growth and on-demand derivation are implemented in Rust with zero external dependencies in `benchmarks/core-math-binary-growth/`.

Under the canonical ontology of #2490:
```text
semantic object = binary number + domain + proved law
```

The growth rule of #2460 is executed directly:
```text
known bits + proved law -> new bits -> reuse new bits
```

### 1. Pure Binary Growth & Chained Derivation
- Binary objects are purely exact-width bit strings (`BinaryNumber`) qualified by an explicit `Domain`.
- Chaining is first-class: newly generated binary objects immediately serve as parents/inputs to subsequent law applications.
- Zero human names, zero per-result registry rows, and zero lookup tables are required or permitted for semantic identity.
- Evaluated across multiple domains:
  - `SelectorPath`: factor extension law `output = 2 * parent + delta` chained to depth 5 (root `101` -> `10101011`).
  - `QGroupFactor`: additive/multiplicative factor laws with role extensions.
  - `AffineFunctionGF2`: monoid of affine endomorphisms in GF(2)^2 (`(A, b) ∘ (C, d) = (A * C, A * d XOR b)`) over 6-bit coordinates.

### 2. On-Demand Derivation (Demand Construction)
- Distinguishes mathematical closure from eager enumeration (#2473, #2474).
- The `DemandEngine` constructs ONLY the required subgraph DAG of intermediate binary nodes needed for a specific derivation target.
- For a depth-3 selector target, demand derivation materializes exactly **4 nodes** (1 root + 3 steps), while eager closure enumerates **15 nodes** (materialization ratio: 4/15).

### 3. Parity Witness
- The bounded `EagerClosureEngine` systematically enumerates all reachable objects up to depth `d`.
- 100% bit-exact parity is verified: every on-demand derived binary object matches bit-for-bit with the corresponding node in the eager closure.

### 4. Falsifier Suite
The implementation satisfies all required falsifiers:
1. **Missing Seed**: Attempting derivation without the necessary seed fails closed with `GrowthError::MissingSeed`.
2. **Missing Law**: Attempting derivation with an unknown law fails closed with `GrowthError::MissingLaw`.
3. **Domain Firewall (#2508)**: Cross-domain law application fails closed with `GrowthError::DomainMismatch`.
4. **Order Invariance**: The order in which independent goals/targets are derived does not alter their semantic objects or bit strings.
5. **Cache Invariance**: Memoization caching does not affect semantic identity; cold vs warm cache executions produce identical binary objects.
6. **Anti-Numerology**: Arbitrary bit permutation or axis swapping destroys the mathematical law and is rejected.

### 5. Architectural Invariants
- Zero external crate dependencies (`[dependencies]` is strictly absent in `Cargo.toml`).
- Execution requires no Lisp runtime, JSON, AST, SHA hashes, or registries.
