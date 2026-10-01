# #2017 — falsification ledger, first verified slice

Research-only. This artifact distinguishes **falsified hypotheses** from
**superseded premises/design choices**.

## Result

The first audit verifies **nine bounded falsification classes**:

1. global Hamming-1 semantic authority;
2. unordered dependency support as prefix authority;
3. named dependency depth as semantic rank;
4. transitive seed-support as semantic rank/identity;
5. evaluator SCC topology as semantic authority;
6. raw `00` as an in-band delimiter for unrestricted packed words;
7. immediate selector-strength EQ children from NULL/EQUAL/MEMBER;
8. immediate selector-strength CONS children from LIST/APPEND/PAIR/PAIRLIS;
9. immediate PredicateBit AND/OR children of COND under current `() != 0`.

The old flat exact-8/256 ontology is **not counted as a falsification**. It is
recorded separately as `superseded-premise`: a design premise can be replaced
without pretending it was a theorem disproved by counterexample.

## Why this distinction matters

The ledger is intentionally monotone only at the correct scope.

For example:

```text
F009 falsifies:
  COND -> PredicateBit AND/OR
  under current answer-contract/2
  as immediate local children

F009 does NOT falsify:
  every possible future typed COND specialization
```

Likewise the CONS/EQ results are bounded negative theorems about the candidate
classes already tested, not universal impossibility claims.

## Minimal counterexamples are the durable part

A row is not accepted merely because an issue says “negative result”. It needs
a counterexample or executable witness that survives renaming.

Examples:

```text
Hamming:
  strong semantic triangle
  vs triangle-free hypercube

unordered support:
  CADR support={CAR,CDR}
  CDAR support={CAR,CDR}
  but ordered paths differ

SCC:
  Lisp I   {eval,evcon,evlis}
  Lisp 1.5 {apply,eval,evcon,evlis}

COND:
  AND(0,0) -> ()
  expected PredicateBit 0
```

## Resurrection rule

`scripts/research-2017-falsification-ledger.py` treats each falsified
`concept_key` as blocked at the recorded scope until the known counterexample
is explicitly invalidated.

A proposal may reopen a concept only by supplying a reason that attacks the
counterexample/assumptions, not by renaming the idea.

The script self-tests deliberate resurrection attempts for all nine falsified
concept keys.

## Scope inflation is forbidden

Do not rewrite:

```text
"the tested EQ candidates do not form immediate selector-strength children"
```

into:

```text
"EQ can never have descendants"
```

The first is evidence. The second is not established.

## Relationship to #2018/#2020/#2016

- #2018 owns epistemic vocabulary/status transitions.
- #2020 owns the matrix of survived attack classes.
- #2016 consumes negative theorems when deriving the maximal generator grammar
  or composition boundary.

This ledger only answers:

> what exactly has already been killed, by what counterexample, and in what scope?
