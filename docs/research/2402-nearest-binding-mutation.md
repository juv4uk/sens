# #2402 — nearest-existing mutation lower bound

Status: research-only. No SET/SETQ implementation and no post-D4 identity is
introduced.

## Boundary already known

D4 DEFINE can already mutate observably when the target lives in the current
frame:

```text
same-frame DEFINE X=NEW
  -> existing closure over that frame sees NEW
```

But from a child frame, DEFINE of an inherited name creates a new child binding:

```text
parent X=OLD
closure P captures parent
child DEFINE X=NEW

child lookup -> NEW
P            -> OLD
```

Therefore generic "value changed" is not a new capability. The surviving
question is whether historical SET/SETQ require **nearest-existing shared
location update**.

## Research countermodel

The test-only helper walks the same `Environment` graph that closures capture:

```text
leaf
 -> parent
 -> ...
 -> nearest frame containing X
 -> replace that existing slot/value
```

It does not create a child shadow and is not exposed to the language.

Observable result:

```text
parent X=OLD
closure P captures parent
child nearest-update X=NEW

child lookup -> NEW
P            -> NEW
child local X binding -> absent
```

This differs from D4 DEFINE under the same initial graph.

## Strong controls

- nearest location wins when two outer frames both contain X;
- farther shadowed location is unchanged;
- missing binding fails closed and creates nothing;
- closure observer is constructed before the candidate update;
- no side table or detached Rust cell is used: the candidate mutates the same
  `Rc<RefCell<Frame>>` graph already captured by closures.

## Interpretation

If the witness survives review:

```text
D4 child DEFINE shadowing
  !=
nearest-existing shared-location update
```

That establishes an observable semantic delta. It still does **not** decide:

- whether historical SET and SETQ are the same operation;
- whether computed targets belong to the same capability;
- exact parent/width/bit placement;
- whether SENS should adopt mutation at all.

Those are later decisions under #2314/#2236.

## Principle

**Mutation earns semantic status only when an observer created before the
operation can tell that the same binding/location changed.**
