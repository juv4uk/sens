# #2107 — incidence below relation

Research-only. This attacks a hidden assumption in `R ⊆ C × C`.

## Core observation

A binary directed relation is not structure-free. To even state one executablely we have already introduced:

```text
distinguishable endpoint occurrences
incidence
ordered endpoint roles (source,target)
and possibly relation-kind labels
```

These must not be credited to a lower foundation unless separately justified.

## Four layers

```text
D  distinguishable points
I  undirected incidence
O  oriented incidence
L  labeled oriented incidence
```

## Orientation witness

Use the same undirected star:

```text
a—b
|
c
```

with two orientations:

```text
out-star: a→b, a→c
in-star:  b→a, c→a
```

The underlying incidence is identical, but the directed degree signatures differ. Therefore the directed graphs are not direction-preserving isomorphic.

So orientation is genuine additional structure; it cannot be said to come 'for free' from incidence.

## Node renaming

Renaming `a,b,c` to arbitrary fresh host tokens changes the carrier representation but preserves graph isomorphism.

Therefore host node identity is a coordinate/gauge choice, not semantic graph meaning.

## Relation labels

A consistent bijective renaming of relation kinds preserves typed structure.

But collapsing two distinct relation roles into one label preserves the bare directed edge set while losing typed information.

Thus relation typing is another independent layer above orientation.

## Consequence for #2103

`R ⊆ C × C` should be treated as a compact notation for a bundle of assumptions, not automatically as FOUNDATION-minus-three.

A safer decomposition is:

```text
distinction / endpoint occurrence
  -> incidence
  -> orientation
  -> relation typing
  -> paths / behavior
  -> observations
```

Which arrow is actually semantic must be proved by the first admitted law that distinguishes the weaker countermodel.

## Remaining deepest question

Even `D = distinguishable points` may be too strong. The next question is whether point identity is primitive, or whether only occurrences/events plus incidence judgments are needed before quotienting by isomorphism/bisimulation.

Artifact: `scripts/research-2107-incidence-foundation.py`.