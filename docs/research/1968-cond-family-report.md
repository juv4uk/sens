# #1968 — bounded COND-family result

Research-only. No allocation/runtime/contracts changes.

## Attractive hypothesis

Because `111 = COND` is the control root, the first idea was to derive two
4-bit predicate connectives:

```text
1110 -> AND
1111 -> OR
```

This would be beautiful if one appended bit selected a partial specialization
of conditional control.

## Current shared law blocks the naïve construction

`contracts/answer-contract.lisp` currently says:

```text
predicate answer = exact one bit: 0 / 1
()               = structural empty, never predicate FALSE
COND clause      = (test expression)
select           = test 1
skip             = test 0
exhaustion       = structural ()
three-part COND  = forbidden
```

Therefore:

```text
AND(p,q) := COND ((p q))
```

does not return PredicateBit `0` when `p=0`; it exhausts to structural
`()`.

Likewise:

```text
OR(p,q) := COND ((p 1) (q 1))
```

exhausts to `()` for `p=0,q=0`, not PredicateBit `0`.

## Executable truth-table result

`scripts/research-1968-cond-family.py` anchors itself to the current
answer contract and exhaustively tests the four PredicateBit input pairs.

Expected failures:

```text
AND: p=0,q=0 -> got (), expected 0
AND: p=0,q=1 -> got (), expected 0

OR:  p=0,q=0 -> got (), expected 0
```

All other rows match.

## Why not “fix” it with ()

Because that would erase one of the strongest current language boundaries:

```text
() != PredicateBit(0)
```

Structural empty is not logical FALSE.

## Could another root repair the construction?

Yes, in principle a second predicate mechanism could manufacture an actual
PredicateBit `0` and a guaranteed PredicateBit `1`.

But then the construction is no longer a small local action of COND alone.
It becomes multi-root, so it does not justify occupying `1110/1111` under
the current generator-first rule.

## Current classification

```text
COND -> predicate AND : typed/control relation only; strong child law not proven
COND -> predicate OR  : typed/control relation only; strong child law not proven

1110 / 1111           : remain unallocated
```

This is bounded negative evidence, not a proof that no richer COND algebra
can ever exist.

## Important distinction from current surface macros

Current `and` / `or` in `lib/core.lisp` are variadic, value-preserving
short-circuit macros. They are not automatically the one-bit PredicateBit
connectives tested here.

Do not identify those surfaces with hypothetical `1110/1111` without a
separate typed semantic proof.

## Principle

**Never buy a beautiful binary family by turning structural emptiness into
logical false.**
