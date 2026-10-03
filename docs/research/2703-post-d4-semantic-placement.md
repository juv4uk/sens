# #2703 — Post-D4 semantic placement of the 19-row historical corpus

Phase: **SENS-DERIVATION**

This report places every completed historical row in the semantic owner graph.
It does **not** allocate new binary residents.

## Resolved derived/mechanism placements

| Historical row | Semantic home | Binary residency |
|---|---|---|
| LABEL | D4 LAMBDA closure/fixed-point recursion | none |
| FUNCTION | D4 LAMBDA closure representation | none |
| FUNARG | D4 LAMBDA + APPLY closure application | none |
| EVALQUOTE | D4 EVAL + APPLY composition | none |
| APPEND | D3 structural recursion | none |
| PAIR | D3 structural recursion | none |
| PAIRLIS | D3 structural recursion over explicit environment tail | none |
| ASSOC | D3 structural search/equality recursion | none |
| SUBST | D3 tree recursion | none |
| SUBLIS | D3 tree recursion + derived ASSOC | none |
| MAPLIST | D4 higher-order application + D3 list traversal | none |
| GO | D1-D4 finite-state dispatch + tail recursion | none |

Important negative placements:
- PAIRLIS is **not** a BIND child;
- ASSOC is **not** a LOOKUP child;
- historical names are retained as provenance, not promoted to residents.

## Surviving post-D4 semantic regions

| Historical row | Semantic region | Current placement |
|---|---|---|
| SET | shared-location carrier | UNPLACED |
| SETQ | shared-location carrier + quoted-target policy | **RATIFIED Core D6 001111** under #2538 OD-001 / #2723 |
| PROG | composite of derived GO + non-local RETURN | no independent resident |
| RETURN | proven non-local-exit root | width UNKNOWN, UNPLACED |
| FEXPR | raw-form + caller-env + invocation carrier family | UNPLACED |
| FSUBR | raw-form + caller-env + invocation carrier family | UNPLACED |
| TRANSFORMER | raw-form carrier + returned-form/timing policy | UNPLACED |

## D5 consequence

The completed D5 SENS-derivation closeout remains unchanged:

```text
selector-generated = 8
UNKNOWN/free       = 24
manual non-selector residents = 0
new non-selector D5 candidates = 0
```

Semantic placement therefore means **putting a historical observation under the
mechanism/family that explains it**, not spending a free coordinate.

## Root/factor consequence

The seven post-D4 structural facts minimize to:

```text
PROVEN-ROOT:
  non-local-exit

CARRIER-PREMISE:
  shared-location-update
  raw-form-input
  explicit-caller-env
  invocation-packaging

POLICY-OVER-ROOT/CARRIER:
  returned-form-protocol
  expansion-timing
```

Roothood still does not determine exact width.

## Reproduce

```sh
python3 benchmarks/post-d4-semantic-placement/run.py --out /tmp/post-d4-placement
```

Expected:

```text
POST-D4-SEMANTIC-PLACEMENT=PASS
HISTORICAL-ROWS=19
NEW-D5-RESIDENTS=0
D5=8-generated+24-UNKNOWN
RETURN=PROVEN-ROOT-UNPLACED
SETQ-D6-001111=RATIFIED-RESIDENT
```

## Principle

**A historical operation can be fully placed in the semantic graph while
having no independent binary resident.**
