# #1962 — vistāra4 frontier: 16 slots, only 4 proven

Це research-only frontier, не allocation table.

## Fixed geometry

Every 4-bit word has a 3-bit structural parent:

```text
000 -> 0000 0001
001 -> 0010 0011
010 -> 0100 0101
011 -> 0110 0111
100 -> 1000 1001
101 -> 1010 1011
110 -> 1100 1101
111 -> 1110 1111
```

But **structural parent does not imply semantic parent**.

## Current evidence

Only four slots have a proven local generator:

```text
1010 = CAAR
1011 = CADR
1100 = CDAR
1101 = CDDR
```

The other 12 remain open.

## Why the open slots matter

The corpus immediately exposes multi-parent candidates:

- `NULL` is related to NIL, ATOM and EQ;
- `LIST` is related to NIL and CONS;
- `EQUAL` extends EQ but also structurally depends on ATOM/CAR/CDR/COND;
- `APPEND` constructs with CONS but also traverses with CAR/CDR and branches with COND;
- `AND/OR/NOT` all plausibly descend from conditional selection, but one COND root has only two 4-bit children.

Therefore a global rule “put each function under its dependency root” is under-specified.

## Typed prefix edges

Use three evidence classes:

1. **generator** — the appended bit itself has a proven local semantic/compositional interpretation.
2. **family** — the node is semantically related to the prefix root, but the bit does not itself derive the node.
3. **allocation-only** — a code is chosen for compression/space efficiency; the prefix carries no semantic-parent claim.

Only class 1 currently supports a theorem.

## Allocation problem

After reserving the four proven selector descendants, `vistāra4` has 12 open words.

The research question is now a constrained graph-compression problem:

```text
choose <= 12 additional nodes
subject to:
  preserve proven generator codes
  do not invent semantic parenthood
  prefer stable Lisp I -> Lisp 1.5 nodes
  maximize reduction in encoded/derived description cost
  keep primary and useful derived nodes in the same width when justified
```

This is intentionally compatible with the owner's point: **primary and derived functions may coexist inside 4 bits**.

## Archaeology guard

The old table's positions 8..15 were:

```text
LAMBDA DEFINE DEFMACRO DEF PLUS DIFFERENCE TIMES DIVIDE
```

That ordering is donor history only. It is not carried forward automatically.

## Next test

Measure candidate value from the bounded corpus using at least:
- cross-era stability;
- structural reuse / caller count;
- normalized expansion cost;
- primary-language necessity;
- local-generator evidence.

Do not assign remaining codes before comparing at least two allocation objectives.
