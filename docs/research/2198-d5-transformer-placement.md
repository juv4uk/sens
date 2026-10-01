# #2198 — D5 transformer placement witness

Status: research-only. The candidate `00101` is **not ratified**.

## Strongest relation: payload identity

The current surrogate path is:

```text
0010 LAMBDA
   -> Value::Closure(Rc<Closure>)
   -> make-macro
   -> Value::Macro(the same Rc<Closure>)
```

The executable witness compares the two runtime values with `Rc::ptr_eq`.

This matters because TRANSFORMER is not merely "related to" LAMBDA. It is a
different invocation mode over the **same closure payload**.

That is a much stronger parent relation than ordinary dependency adjacency.

## Competing D4 parents

### DEFINE

DEFINE can bind a transformer value, but it can bind many other values too.
It does not construct or refine the transformer body.

### APPLY

APPLY consumes an already-resolved callable. It does not create transformer
identity or raw-form invocation mode.

### EVAL

EVAL consumes/interprets forms. It does not create the closure that becomes a
transformer.

### LAMBDA

LAMBDA creates exactly the payload that the transformer constructor accepts,
and the constructor preserves that payload identity.

Therefore LAMBDA is currently the strongest semantic parent.

## Candidate coordinate

```text
0010   LAMBDA
00101  TRANSFORMER   ; candidate
```

The final bit `1` is still a hypothesis. It reuses the ratified weak D4
polarity:

```text
0 = current/focus/resolved
1 = continuation/context expansion
```

A transformer delays ordinary operand evaluation, produces code, and re-enters
evaluation in caller context, so `1` is the better current fit.

But this is not a proven universal D5 suffix theorem.

## Why 00100 stays empty

Ordinary closure construction already has the exact-width parent identity
`0010`. Allocating `00100` merely to mean "ordinary LAMBDA again" would
duplicate semantics without a new observable capability.

Therefore the research model keeps:

```text
00100  unallocated
00101  TRANSFORMER candidate
```

unless counterevidence appears.

## Executable witnesses

- Closure -> transformer preserves exact Rc payload identity.
- Non-closure materialization fails closed.
- Same closure body has eager ordinary invocation and raw staged invocation.
- Candidate word does not collide with the fixed D5 selector subtree.
- Zero-child remains an explicitly non-allocated research position.

## Principle

**Place a D5 child beneath the operation whose value it refines, not beneath
the operation that merely consumes or binds it.**
