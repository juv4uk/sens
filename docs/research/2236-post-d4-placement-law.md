# #2236 — post-D4 placement law

Status: research-only.

The post-D4 reset changes the placement question from:

```text
which free D5 word should receive the next feature?
```

to:

```text
which historical capability is still irreducible after D1-D4,
and does exactly one new binary distinction refine an existing parent?
```

## Law

A width-`N+1` child is eligible only when:

```text
same base semantic object/operation
+ exactly one observable new distinction
= child
```

The child therefore explains itself as a local construction path rather than a
slot in a flat table.

The search order is:

1. already represented;
2. derived in Lisp;
3. local generated child;
4. residue;
5. wider width if more than one independent new distinction is required.

Empty addresses are a successful result.

## Observable delta vector

Before a child may consume one extra bit, the proposed parent/child relation
must name the independent observable changes.

For a one-bit child:

```text
same base object = yes
independent delta axes = exactly 1
```

This is not a global semantic-distance metric. It is a local falsifier after a
parent relation has already been proposed.

Current LABEL comparison:

```text
LAMBDA -> LABEL
  base object: closure/callable
  delta axes: local-self-binding
  count: 1

DEFINE -> LABEL
  base object: persistent binding operation -> closure value
  delta axes:
    base-object-kind
    binding-lifetime
    local-self-reference
  count: >1
```

Therefore the DEFINE counterplacement does not currently qualify as a one-bit
generated child.

## Bit orientation

The D4 weak polarity may be reused only where the executable relation fits:

```text
0 = current / focus / resolved
1 = continuation / context expansion
```

This does not replace family-specific stronger laws. Selector descendants keep:

```text
0 = compose CAR
1 = compose CDR
```

## Resolved first consumer — LABEL

#2234 / #2238 resolved the first historical candidate:

```text
LABEL=DERIVED-D4
address=none
```

Current Core1's historical LABEL branch does not install self-binding, but D4
LAMBDA can derive local recursion through an applicative fixed point. A stronger
witness returns an escaping recursive closure with lexical capture and an
alpha-renamed self variable, without LABEL or DEFINE.

Therefore:

```text
0010  LAMBDA
00101 <unallocated>
```

The earlier `00101 LABEL` shape remains only a counterfactual used to test the
placement law. It is not an active candidate.

## LABEL hypothesis

Historical shape:

```text
LABEL(name, lambda)
= LAMBDA-like callable
+ local recursive self-binding
```

If #2234 proves that this self-binding is an irreducible observable capability,
the strongest current placement hypothesis is:

```text
0010   LAMBDA
00101  LABEL      ; candidate only
```

Why suffix 1 is plausible:

- the base object remains a closure/callable;
- the one new delta is a binding added to the closure's evaluation context;
- that is a direct fit to the existing weak "context expansion" orientation.

This is not ratified. The script explicitly preserves the opposite outcome:

```text
if LABEL is derivable from D4:
  LABEL -> no address
  00101 -> remains unallocated
```

## Counterplacement

LABEL under DEFINE is weaker at present:

```text
0011 DEFINE
  ? -> LABEL
```

DEFINE extends persistent/global binding state. Historical LABEL localizes a
self-reference around a function expression. Until an executable witness shows
they are the same base semantic object plus one delta, that parent relation is
not admitted.

Likewise:

```text
0101 LABEL
1001 LABEL
```

would be allocation-only uses of free D4 capacity and are not placement laws.

## One child word cannot carry two independent axes

An exact parent/suffix pair is one construction path. Therefore two independent
semantic refinements may not silently claim the same child word.

This matters immediately for the historical reset:

```text
0010  LAMBDA

candidate A:
00101 LABEL
delta axis = local-self-binding

old candidate B:
00101 TRANSFORMER
delta axis = raw-staged-invocation
```

If both deltas survive as independently observable capabilities, D5 is too
narrow to encode both under the same LAMBDA+1 edge.

Allowed outcomes are then:

```text
derive one capability
find a different honest parent for one capability
move one/both refinements to a wider stratum
```

Not allowed:

```text
same exact word = two unrelated semantic refinements
```

This gives the historical ordering real force: LABEL is tested first because it
appears earlier in the Lisp lineage, not because it is preferred aesthetically.

## Historical search order

The current ladder is intentionally unresolved:

```text
LABEL
FUNCTION/FUNARG
EVALQUOTE
APPEND
PAIR/PAIRLIS
ASSOC
SUBST/SUBLIS
MAPLIST
SET/SETQ
PROG/GO/RETURN
```

For each candidate, the strongest plausible parent is tested before residue:

```text
FUNCTION/FUNARG -> LAMBDA
EVALQUOTE       -> EVAL/APPLY
PAIR/PAIRLIS    -> BIND/structure
ASSOC           -> LOOKUP
SET/SETQ        -> DEFINE/BIND, but mutation must be proven as one delta
```

Most historical names are expected to disappear as derived or
historical-mechanism-only. That expectation is not a result.

## Reproduce

```sh
python3 scripts/research-2236-post-d4-placement-law.py
```

Expected headline:

```text
POST-D4-PLACEMENT-LAW=PASS
LABEL-IF-DERIVED=NO-ADDRESS
LABEL-IF-ONE-DELTA-GAP=00101
LABEL-DEFINE-COUNTERMODEL=RESIDUE
```

## Principle

**History proposes the next question. A local semantic generator earns the next
bit. Free capacity earns nothing.**
