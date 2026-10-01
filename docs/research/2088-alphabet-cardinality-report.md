# #2088 — alphabet cardinality beneath the binary-word law

Research-only. No production identity change.

## Why this exists

#2077 currently proposes canonical identities as finite non-empty words over `{0,1}`.

That statement bundles three different propositions:

1. exact words need a sequence alphabet;
2. the alphabet must contain at least two symbols;
3. the exact canonical symbols must be `0` and `1`.

This slice separates them.

## A — exact identity alone does not force binary

A unary alphabet can still form distinct exact words:

```text
•
••
•••
••••
...
```

If width participates in identity, these words remain distinct.

So the generic law:

```text
identity = exact width + exact symbol sequence
```

does **not** by itself derive alphabet cardinality 2.

## B — two distinct immediate refinements do force cardinality >= 2

For a parent `p`, one-symbol children are:

```text
{ p+s | s in alphabet }
```

so the number of distinct immediate children is at most the alphabet cardinality.

A unary alphabet gives exactly one immediate child.

If an admitted semantic law requires two distinct one-step refinements:

```text
p -> p+a
p -> p+b
p+a != p+b
```

then alphabet cardinality must be at least 2.

This is the right kind of lower bound for CAR/CDR-style `T0/T1` generation, but it is **family-dependent evidence**. It must not be silently promoted to a generic identity theorem.

## C — exact symbols `0/1` are not pinned by the structural law

The executable witness constructs a bijection:

```text
0 <-> α
1 <-> β
```

and verifies that it preserves:
- exact equality;
- width;
- prefix;
- parent;
- append;
- two-branch path structure.

Therefore, once a 2-symbol alphabet is required, the structure derives:

```text
two distinguishable refinement symbols
```

not the glyphs/names `0` and `1` themselves.

## Epistemic consequence

A more precise #2077 wording may need to distinguish:

```text
word-sequence role                 candidate foundation law
alphabet cardinality >= 2          derived only for two-branch families
canonical representatives 0/1      ratified representation choice unless independently derived
```

That does not weaken binary SENS. It tells us exactly which part is mathematical lower bound and which part is canonical convention.

## Non-conclusion

This does not argue for changing SENS away from binary.

It says only: if binary is foundational, state the assumption/evidence that makes it foundational rather than crediting generic exact identity with a proof it does not supply.

Artifact: `scripts/research-2088-alphabet-cardinality.py`.