# #2441 — Lisp 1.5 SET/SETQ historical semantics

Status: research evidence for Phase D.

Primary source: *LISP 1.5 Programmer's Manual*, MIT Press, 1962.

Source:
https://softwarepreservation.computerhistory.org/LISP/book/LISP%201.5%20Programmers%20Manual.pdf

## Result

The historical interpreter semantics match the lower-bound shape isolated by #2402:

```text
HISTORICAL-SETQ=SHARED-LOCATION-UPDATE
```

Appendix B states operationally that SET/SETQ:

1. locates the variable name on the current association list;
2. replaces the value cell of that existing binding pair;
3. if the name occurs more than once, changes the first / most-recent binding;
4. if that binding was established at a higher level, the changed value remains in effect for the rest of that binding's scope;
5. signals the historical A4/A5 error when the name is absent instead of creating a new binding.

The Chapter V PROG discussion also states that SET/SETQ can change variables on the a-list of higher-level functions.

## SET vs SETQ

The mutation target is the same binding mechanism:

```text
SET   : evaluate first argument to obtain the variable name
SETQ  : quote the first argument
```

Both return the value of the second argument.

## Comparison to #2402

```text
#2402 lower bound                     Lisp 1.5 manual
--------------------------------------------------------------
update existing location              yes
nearest existing binding              yes: first / most recent
no new child binding on miss          yes: A4/A5 error
higher-level observer sees update     yes within that binding scope
computed target vs syntax-fixed       SET vs SETQ
```

## Important caveat

The historical carrier is the dynamically scoped a-list binding pair.

Do not rewrite the result as:

```text
Lisp 1.5 required a modern lexical closure cell
```

The source supports the narrower statement needed by #2402:

```text
the same already-existing a-list binding pair is mutated in place,
and subsequent observation through that binding sees the new value
```

This pins the historical target. It does not decide whether SENS D4 can derive the observation through explicit state passing. #2442 owns that attack.

## Consequence

#2314 should now use this historical target:

```text
nearest-existing shared binding/location update
```

but remain UNRESOLVED until #2442 decides whether that observation is D4-derivable without hidden mutable host state.

No address or width follows from this report.
