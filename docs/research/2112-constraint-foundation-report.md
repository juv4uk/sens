# #2112 — constraint status before relation extension

Research-only. No production migration.

## Question

An extensional relation is usually written as the set of positive facts:

```text
R = { admitted candidates }
```

but in an open research language that representation loses the distinction between:

```text
REFUTED
UNKNOWN
```

because both are merely absent from `R`.

## Candidate lower layer

For a bounded possibility space Ω, assign each candidate one status:

```text
ADMITTED
REFUTED
UNKNOWN
```

This is not a program PredicateBit. It is meta-semantic status of a proposition/fact candidate.

## Complete-world result

If every candidate is decided, then:

```text
ADMITTED = Ω \ REFUTED
REFUTED  = Ω \ ADMITTED
```

So in a genuinely complete closed finite model, positive and negative extensions are dual.

## Open-world counterexample

Construct two models with the same positive extension:

```text
A: p admitted, q refuted,  r unknown
B: p admitted, q unknown,  r refuted
```

Both produce:

```text
positive relation = {p}
```

but they carry different knowledge.

Likewise two models can share the same negative/refuted extension while differing in which remaining candidates are admitted vs unknown.

Therefore:

```text
positive extension alone  loses REFUTED vs UNKNOWN
negative extension alone  loses ADMITTED vs UNKNOWN
```

## Closed-world assumption

The executable witness implements an explicit policy:

```text
UNKNOWN -> REFUTED
```

and verifies that it changes the model.

So closed-world reasoning is an additional law/policy. It is not contained in the primitive status data.

## Renaming

Bijective renaming of candidate fact tokens preserves the status structure, while host token equality changes.

Thus proposition labels are again coordinates/mechanism; the admitted/refuted/unknown pattern is the modeled content.

## Consequence for relation/composition layers

#2103/#2107 relation facts should be interpreted, when evidence is incomplete, as the **ADMITTED slice** of a richer status assignment.

#2017 falsifiers naturally occupy the **REFUTED slice**.

Everything else must remain UNKNOWN unless a separate completeness/closed-world theorem says otherwise.

This is orthogonal to:
- #2108 consequence rules;
- #2104 judgment syntax;
- #2107 incidence/orientation content.

## Foundational consequence

A safer current ladder is:

```text
candidate possibility / proposition
  -> admitted | refuted | unknown
  -> incidence/orientation/composition facts
  -> consequence/proof
  -> observations/equivalence
  -> identities/words/binary
```

The exact bottom is still open because even `candidate possibility` may hide identity/occurrence assumptions.

Artifact: `scripts/research-2112-constraint-foundation.py`.