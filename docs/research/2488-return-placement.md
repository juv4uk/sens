# #2488 — RETURN parent/width placement falsifier

Status: research-only.

## Canonical ontology

```text
DOMAIN        Core post-D4 placement
BINARY OBJECT no coordinate admitted
LAW           dynamic exit target/context policy
WITNESS       executable policy square
FALSIFIER     D4 parent tournament
STATUS        hypothesis under executable attack
RELATION      Core-only
```

## Proven input

Historical RETURN has already survived Phase D as a source-level capability:

> deliver a value to the most-recent active PROG exit across ordinary call
> boundaries.

It is globally compilable to D4 by CPS, but #2468 shows that doing so rewrites
the call-chain protocol and therefore does not locally derive the source
capability.

## Two-axis factorization

Ordinary D4 completion is modeled as:

```text
target  = immediate caller
context = optional
```

Historical RETURN core is:

```text
target  = nearest active PROG
context = required; fail if none
```

The executable witness evaluates all four combinations:

```text
                     optional              required
immediate            ordinary              immediate+guard
nearest-PROG         soft dynamic exit     historical RETURN
```

Both axes are independently observable.

### Axis 1 — target selection

With one active PROG and the same required-context policy:

```text
immediate -> immediate caller
nearest   -> active PROG
```

### Axis 2 — context requirement

With no active PROG and the same target policy:

```text
optional -> ordinary fallback
required -> fail closed
```

Therefore ordinary completion and historical RETURN differ by two independent
observable policy axes.

## Parent tournament

The post-D4 placement law requires the parent to own the same base semantic
operation.

```text
APPLY   callable + values -> invoke callable
EVAL    form -> evaluate form
LAMBDA  parameters/body -> construct closure
COND    predicate/branches -> local branch selection
RETURN  value + active dynamic context -> non-local transfer
```

None of the D4 candidates owns that same base operation.

CPS may represent the exit continuation with a closure, but representation is
not LAMBDA parenthood. EVAL/APPLY participate in execution around RETURN, but
participation is not semantic parenthood. COND is local branch selection and
does not own a dynamic exit target.

## Current result under test

```text
RETURN-ROOT=RESIDUE
EXACT-DOMAIN=UNRESOLVED
BINARY-COORDINATE=UNALLOCATED
```

This means only:

- reject decorative D5 child placement under APPLY/EVAL/LAMBDA/COND;
- preserve RETURN as an independently justified post-D4 semantic root;
- defer D5 vs D6 and exact coordinate until a separate residue/domain law earns
  them.

It does **not** allocate a free D5 cell.

## Principle

**When no parent owns the same operation, do not turn implementation adjacency
into a prefix. A real semantic root may remain residue until its domain law is
proved.**
