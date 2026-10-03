# #2344 — Early-Lisp historical ingest ledger

Status: **HISTORICAL-INGEST**. This ledger is evidence bookkeeping, not language semantic authority.

Machine source:

```text
docs/research/2344-post-d4-historical-ledger.json
```

Validator:

```text
scripts/research-2344-historical-ledger.py
```

## Current chronology

Completed:

```text
LABEL            DERIVED-D1-D4
FUNCTION/FUNARG  HISTORICAL-MECHANISM
EVALQUOTE        DERIVED-D1-D4

APPEND            DERIVED-D1-D4
PAIR/PAIRLIS      DERIVED-D1-D4
ASSOC              DERIVED-D1-D4
SUBST/SUBLIS      DERIVED-D1-D4
MAPLIST            DERIVED-D1-D4

SET/SETQ           NEW-OBSERVABLE-CAPABILITY
GO                 DERIVED-D1-D4
RETURN             NEW-OBSERVABLE-CAPABILITY

FEXPR/FSUBR        RAW+ENV-TWO-CAPABILITIES
```

Active:

```text
TRANSFORMER / later macro staging -> #2557
```

## Phase-D nuance

Whole-program compilation does not erase a source capability.

```text
SET/SETQ shared-location update
  = NEW-OBSERVABLE-CAPABILITY
  + COMPILABLE-TO-D4-GLOBAL

GO
  = DERIVED-D1-D4 locally

RETURN
  = NEW-OBSERVABLE-CAPABILITY
  + COMPILABLE-TO-D4-GLOBAL
```

This follows the derivation law in #2468.

## Phase-E protocol

Historical FEXPR/FSUBR:

```text
raw operands        = 1
explicit caller env = 1
result re-eval      = 0
```

Current SENS transformer comparison:

```text
raw operands        = 1
explicit caller env = 0
result re-eval      = 1
```

The shared raw-operand axis does not collapse the protocols into one capability.

## Placement boundary

Every row in this ingest ledger keeps:

```text
binary_object = unplaced
```

even when later SENS analysis already says a historical operation is derived or exposes a new capability.

The generated D5 selector subtree remains a separate baseline fact:

```text
10100 10101 10110 10111
11000 11001 11010 11011
```

It does not terminate the historical inventory.

## Gate

While #2557 is active:

```text
historical-ingest-complete = no
structural-discovery-may-start = no
placement-search-may-start = no
```

## Principle

**History is collected first. Structural laws explain it second. Native SENS coordinates come third.**
