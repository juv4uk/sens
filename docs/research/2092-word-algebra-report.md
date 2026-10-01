# #2092 — weakest word algebra, first executable comparison

Research-only. No production migration.

## Models

The same bounded identity/path obligations are tested against four deliberately different algebras:

```text
A  free semigroup Σ+
B  free monoid Σ*
C  opaque exact identities + external parent relation
D  productive paths with one-step refine/parent only
```

## Why C and D matter

If C satisfies exact identity/extent while exposing no concatenation at all, then exact identity alone cannot prove that concatenation is language law.

If D supports a two-child generated path with only:

```text
refine(parent, one_symbol)
parent(child)
```

then a generator family does not require a total:

```text
concat : W × W -> W
```

either.

## What A/B additionally provide

A and B have free-word concatenation and cancellation.

B additionally has a neutral element ε.

Those properties may be useful or eventually derivable, but this witness asks whether they are **required by current admitted obligations**.

## Expected classification

```text
property                 identity-only   productive path   full semigroup/monoid
exact identity              required        required              required
extent                       required        required              required
one-step refinement          no             required              available
parent relation              no             required              available
arbitrary concatenation      no             no                    yes
neutral ε                    no             no                    monoid only
cancellation                 no             local injectivity      free words
```

## Boundary result

The witness also encodes multiple words using external `(extent,payload)` metadata. No delimiter symbol becomes part of identity.

This reinforces the separation:

```text
identity algebra != container/framing algebra
```

## Foundational consequence

The current evidence should not ratify a stronger algebra than necessary.

For the present scope:

- identity-only claims admit an opaque-identity countermodel;
- CAR/CDR-style generation admits a productive-path model;
- neither requires arbitrary word concatenation;
- semigroup/monoid laws remain additional candidate structure.

That means #2077/#2091 can safely specify exact identity without silently inheriting every operation host strings happen to support.

Artifact: `scripts/research-2092-word-algebra.py`.