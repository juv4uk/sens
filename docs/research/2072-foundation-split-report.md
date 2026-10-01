# #2072 — first structural lower-bound slice

Research-only. This does not ratify a replacement bīja3.

## Question

Before asking whether the eight inherited bīja3 entries are minimal, ask whether they are even one homogeneous kind of basis.

The first slice isolates a **value/data algebra** and deliberately excludes evaluator-control assumptions.

Abstract roles under test:
```text
ground
make-pair
left
right
atom-class
atom-identity
choose
```

Historical primitive names are not used as proof.

## Method

For each target role, remove it and enumerate all well-typed expressions up to size 9 from the remaining roles over an adversarial finite value universe.

Expressions are deduplicated extensionally, so the search counts semantic functions rather than syntactic spellings.

A failed bounded search is supporting evidence only. Each case also carries an information/invariance witness that a later formal proof can strengthen.

## Lower-bound ideas

### left
For a pair `(a . b)`, the desired result `a` is outside the subvalue closure reachable by repeatedly following only the right projection. Pair construction can wrap reachable values but cannot reveal the hidden left component.

### right
Symmetric argument.

### make-pair
On atomic runtime inputs `a,b`, without a constructor the remaining value operations may select/test/project existing values but cannot manufacture the fresh structure `(a . b)` whose two components independently depend on the two inputs.

### atom-identity
Without a binary atom-identity observer, `(a,a)` and `(a,b)` have the same unary atom-class observations. Any proof must explain what remaining operation could observe the difference without smuggling identity back in.

### atom-class
Without an atom/pair classifier, projection and atom-identity probes are partial on opposite sides of the partition. The first slice forbids treating host errors as a hidden branch/catch oracle.

## Critical non-conclusion

This does not yet prove these five roles are logically independent in every possible language.

It proves something narrower and important:

> the current structural roles are not trivially reconstructible from one another by small compositions in the admitted abstract algebra, and each has a distinct information-lower-bound candidate.

## Why this matters for bīja3

The old 0+7 bundle combines at least two kinds of questions:

```text
value algebra:       what values exist and how structure is built/observed?
evaluator/control:   which expressions are evaluated, suppressed, selected?
```

`QUOTE` and `COND` should therefore not be allowed to prove minimality of the value algebra until their evaluator assumptions are stated separately.

Next slice: formalize the five invariants and then test the two hardest points:
- whether some abstract `ground` role is necessary while exact `()` remains a chosen representative;
- whether evaluator control can be layered above the value algebra rather than co-equal with it.

Artifact: `scripts/research-2072-foundation-split.py`.