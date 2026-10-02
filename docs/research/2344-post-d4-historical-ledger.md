# #2344 — Lisp I -> Lisp 1.5 historical capability ledger

Status: research evidence ledger, not semantic authority.

The question is chronological:

> after removing every behavior already represented or derivable from D1-D4,
> what is the first surviving new observable capability?

The machine source is:

```text
docs/research/2344-post-d4-historical-ledger.json
```

The validator is:

```text
scripts/research-2344-historical-ledger.py
```

## Current resolved rows

```text
LABEL       DERIVED-D1-D4
FUNCTION    HISTORICAL-MECHANISM
FUNARG      HISTORICAL-MECHANISM
EVALQUOTE   DERIVED-D1-D4
PAIRLIS     DERIVED-D1-D4
```

Important negative result:

```text
PAIRLIS != current BIND
```

Historical PAIRLIS preserves a parameter/value batch order while current
C1-BIND reverses that batch. PAIRLIS is nevertheless ordinary structural
recursion, so role similarity did not earn BIND parenthood or a new identity.

## Intentionally unresolved

The ledger keeps gaps visible:

```text
APPEND
PAIR
ASSOC
SUBST
SUBLIS
MAPLIST
SET / SETQ
PROG / GO / RETURN
FEXPR / FSUBR
TRANSFORMER
```

PAIR is deliberately unresolved even though it looks trivial: #2286 proved
PAIRLIS, not a separate PAIR derivation witness. The ledger must expose that
difference rather than promote intuition to evidence.

## Mechanical rules

A completed row must:
- have a non-UNRESOLVED classification;
- cite a full 40-hex git commit;
- point to a commit that exists in repository history;
- state whether hidden state / caller environment / one-new-delta are needed.

An unresolved row must:
- cite no merged evidence SHA;
- allocate no address.

This ledger version allocates **no post-D4 address at all**.

## Closeout

The validator computes:

```text
first-new-observable-capability
earliest-unresolved
placement-search-may-start
```

Placement may start only after the first surviving new capability is known and
every earlier historical row is resolved.

## Principle

**History chooses the next question. Executable derivation decides whether the
name survives. Placement comes last.**
