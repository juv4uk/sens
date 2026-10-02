# #2402 — SET/SETQ shared-location lower bound

Status: research-only. No address or production mutation operator is introduced.

## Live D4 boundary

Merged #2392 already proves that DEFINE is not purely immutable:

- same-frame redefinition changes an existing current-frame slot;
- top-level redefinition is visible to an already-created closure;
- child-frame DEFINE of an inherited name constructs a child shadow;
- a runtime-computed DEFINE target is rejected.

So the post-D4 question is narrower than “does a value ever change?”

## Surviving observation

The bounded countermodel adds exactly one behavior:

> From a child frame, find the nearest already-existing lexical location and update that same location without constructing a new child binding.

```text
parent X = OLD
observer-before captures parent X
child inherits X

D4 child DEFINE X = NEW
  child gets a shadow
  observer-before -> OLD

nearest-existing update X := NEW
  no child X is created
  observer-before -> NEW
  child lookup     -> NEW
  observer-after   -> NEW
```

The countermodel also pins lexical shadowing:

```text
root X
  middle X
    leaf performs update X

only middle X changes
root X remains unchanged
```

A missing name fails closed instead of silently creating a binding.

## What the model does not claim

The test-only Rc<RefCell<_>> location is representation, not semantic authority. It is used only to make “same location” observable.

This evidence does not yet assign:
- a historical surface name;
- a D4/D5 address;
- a parent word;
- a production storage mechanism.

## Provisional semantic conclusion

Current D4 operations do not expose the specific nearest-existing outer-location update observed above. D4 child DEFINE instead creates a shadow.

Therefore the first Phase-D mutation candidate is not “rebind a name” but:

```text
shared-location update
```

This is the exact delta #2314/#2236 should classify before any placement work.

## Principle

**Mutation is new only where an old observer can prove that the same location, not a newly constructed shadow, changed.**
