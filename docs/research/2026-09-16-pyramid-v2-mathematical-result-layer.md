# Logic pyramid v2 — insert the mathematical-result layer

Issue: #225  
Governing architecture: #222  
Research branch: `research/223-many-valued-logic`  
Date: 2026-09-16  
Status: owner architecture correction

## Why the correction was necessary

The previous research split was too coarse:

```text
exact ℚ binary
    vs
richer / many-valued logic
```

That incorrectly pushed mathematical objects such as `pi`, `sqrt(2)`, rational approximations, intervals and exact-real representations into many-valued logic merely because they are not exact binary YES/NO outcomes.

The corrected rule is:

> **Mathematics stays mathematics.** Exact YES/NO is only the narrow top decision layer of mathematics. Every other mathematical answer belongs to a separate mathematical-result floor. Many-valued logic begins only after mathematical territory ends.

## Corrected pyramid

```text
                         ()
          all possible answers / no answer
                         |
                         v
              EXACT BINARY MATHEMATICS
                    ℚ-only decisions
                 0/1 NO | 1/1 YES
                         |
                         v
               MATHEMATICAL RESULTS
       all non-binary answers that are still math
                         |
      exact rationals / arithmetic values
      rational approximations / intervals
      algebraic irrationals / transcendentals
      symbolic expressions / exact-real objects
      precision / error / enclosure metadata
                         |
                         v
                MANY-VALUED LOGIC
           non-mathematical reasoning only
                         |
          evidence / conflict / ignorance
          proof / provenance / semantics
          vague predicates / world-model states
                         |
                         v
                        ()
```

## Floor ownership

### `()`

`()` is literally the empty list. Architecturally it is also the canonical zero-result/no-answer boundary. It is not FALSE, UNKNOWN, NEITHER, conflict, or any other truth value.

### Exact binary mathematics

This is the narrow decision sublayer already defined by #216.

```text
0/1 = exact NO
1/1 = exact YES
```

Only exact rational mathematical decisions belong here.

### Mathematical-result layer

Owned by #225.

This floor contains mathematical answers that are not the binary decision values themselves, including:

- integer/rational arithmetic results;
- rational approximations;
- intervals/enclosures;
- algebraic irrational values such as `sqrt(2)`;
- transcendental/symbolic values such as `pi`;
- exact-real representations;
- symbolic expressions;
- converging approximation objects;
- precision/error/enclosure metadata.

Examples:

```lisp
(+ 1/3 1/6)       => 1/2
(pi)              => mathematical object/value
(approx pi 20)    => rational approximation or enclosure
(sqrt 2)          => exact algebraic/symbolic object if supported
```

The governing invariant is:

```text
non-binary mathematical result != many-valued truth value
```

### Many-valued / richer logic

Owned by #224 and researched in #223.

It begins only after mathematics ends. It is for non-mathematical reasoning such as:

- incomplete knowledge;
- conflicting evidence;
- support/refutation states;
- proof/provenance about world facts;
- semantic/linguistic classification;
- vague predicates;
- epistemic uncertainty;
- nonmonotonic/default reasoning;
- agent/world-model states.

No single algebra is ratified yet.

## Sovereignty law

Semantic authority flows downward only.

A lower floor may specialize only delegated territory and MUST NOT:

1. redefine `()`;
2. reinterpret `0/1` or `1/1`;
3. expand the ℚ-only binary decision contract;
4. reinterpret mathematical objects/results as many-valued truth states;
5. make internal statuses universal language truth values;
6. impose lower-floor control semantics on upper floors.

Removal test:

```text
remove many-valued floor
    -> mathematics unchanged

remove extended mathematical-result machinery
    -> exact ℚ binary unchanged
```

## Consequence for the running many-valued research

Earlier research notes that placed non-ℚ mathematics inside the many-valued territory are superseded on this point.

The exact-real/domain-theory literature discovered in Pass 1 remains useful, but it now belongs conceptually to #225: it supports representing non-rational mathematical objects and approximation structures as mathematical data, not as many-valued truth.

The many-valued research should now evaluate Belnap/FDE, bilattices/Fitting, LP, K3, AFT, multi-adjoint and related frameworks only for the **non-mathematical reasoning floor** and for their interface to mathematical result objects.

## Research interface question

The next important question is not “how does many-valued logic represent `pi`?” It is:

> How can a non-mathematical reasoner attach evidence, proof, uncertainty, provenance or conflict to propositions that may contain mathematical result objects, while leaving those mathematical objects semantically untouched?

Example conceptual separation:

```text
mathematical object:
    pi

mathematical result:
    interval(3.14159..., 3.14160...)

non-mathematical reasoning state about a claim/source:
    support / refutation / conflict / provenance
```

These are different floors and must remain distinguishable.

## Required future witnesses

1. exact rational proposition -> `0/1` or `1/1`;
2. exact rational calculation -> rational arithmetic value;
3. `pi` / `sqrt(2)` -> mathematical object/result, not logical status;
4. rational approximation -> mathematical data;
5. interval enclosure -> mathematical data;
6. conflicting world evidence -> many-valued state;
7. a richer reasoner may refer to mathematical objects without owning their semantics;
8. no answer -> `()`;
9. lower-floor removal leaves upper floors unchanged.

## Principle

**Exact binary logic is a narrow mathematical decision layer. Arithmetic, approximation, symbolic and non-rational results remain mathematics. Many-valued logic starts only after mathematics ends.**