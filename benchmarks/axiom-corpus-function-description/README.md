# Axiom-corpus function description (#3451 / #3454)

This witness describes current exact D5 binary function identities from what
they do to admitted/derived exact rational constants.

Human function names are not used by the test.

Function identities:

```text
D5:01010
D5:01011
D5:10110
D5:10111
```

## Primitive ground

Candidate primitive seed corpus:

```text
{-1, 0, 1}
```

No single ordered pair drawn only from that set separates all four functions:
at least two exact identities collide on every one-tuple probe.

## Language-grown distinguishing fact

The runtime itself derives:

```text
D5:01010(1,1) -> 2
```

Using the derived constant, the single tuple `(1,2)` gives the name-erased
action signature:

```text
01010 -> 3
01011 -> -1
10110 -> 2
10111 -> 1/2
```

All four results are distinct.

So a derived constant does real bootstrap work: it increases the language's
ability to describe and distinguish its own binary functions without adding a
new primitive name or table row.

The next slice should extend the same method to:
- the minimal seed basis from #3420;
- the seven name-erased world axioms from #3386/#3434;
- MODEL_LAW/world derivations from #3402/#3397.
