# #2076 — ground role vs exact `()`

Research-only. This attacks the deepest current bīja3 assumption: `000 -> ()`.

## Question

Do the structural value laws derive the exact identity `()`, or only a distinguished zero-arity ground/terminator role?

## Two-world witness

Construct two models with identical structural shape:

```text
M0 ground = g0
M1 ground = g1
```

A recursive bijection maps `g0 -> g1`, preserves ordinary atoms, and maps pairs componentwise.

The witness checks that the following commute with the bijection:
- make-pair;
- left;
- right;
- atom-vs-pair classification;
- atom identity;
- proper-list termination shape.

To avoid depending on the still-delicate ground/EQ-domain question, the test runs two policies:

```text
ground not admitted to atom identity
ground admitted reflexively to atom identity
```

The isomorphism must survive both.

## Meaning of a successful isomorphism

If all formulas built only from the modeled structural signature are invariant under the isomorphism, then that signature cannot distinguish `g0` from `g1` as the *exact* ground representative.

It can still require:

```text
there exists a distinguished ground/terminator role
```

without deriving:

```text
that role must be the exact current object spelled ()
```

## What may still pin exact `()`

Any of these could add the missing distinction, but they must be named explicitly:
- reader/source syntax;
- evaluator/QUOTE law;
- explicit owner-ratified identity law;
- another semantic relation not present in the value algebra;
- an independent physical/WSM derivation.

Those are additional premises. They cannot be credited to the structural algebra retroactively.

## Epistemic consequence for bīja3

If the witness survives independent review, the status of `000 -> ()` should be split:

```text
ground-role necessity          open / to be proved
exact () as representative     premise unless separately derived
```

This would be the first direct evidence that the inherited bīja3 codes mix an abstract semantic role with a historically chosen representative.

Artifact: `scripts/research-2076-ground-role.py`.