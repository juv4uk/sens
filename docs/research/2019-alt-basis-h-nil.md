# Alternative basis H-NIL (#2019)

**Agent:** grok-xai  
**Epistemic status:** **conjecture** (not theorem, not production)  
**Parent matrix:** `2019-seed-necessity.md`  
**Lock:** does **not** change #2018 `bija3-seed=premise` and does **not** reassign codes

## Hypothesis

```text
H-NIL:
  The operator bīja3 need not contain NIL/000 as a root operation.
  Canonical empty is data (structural ()), not an operator seed.
```

Proposed **operator** seed (size 7):

```text
001  QUOTE     evaluation_control
010  ATOM      type_predicate
011  EQ        identity_predicate
100  CONS      pair_constructor
101  CAR       pair_destructor
110  CDR       pair_destructor
111  COND      conditional_control
```

`000` / `()` remains available as **data / ground value**, possibly aligned with racanā/structure, not as a member of the operator seed table.

## What H-NIL claims

| claim | meaning |
|-------|--------|
| Smaller operator basis | 7 roots instead of 8 |
| Category split | operators vs ground data |
| No loss of pair calculus | CONS/CAR/CDR unchanged |
| No loss of control | QUOTE/COND unchanged |

## What H-NIL does **not** claim

- that current production runtime should drop NIL;
- that code `000` is free for a new operator;
- that Lisp surface without a NIL *name* is required;
- that bīja3 is now derived or minimal.

## Smuggling audit

| reconstruction pressure | smuggles NIL-as-operator? | verdict |
|-------------------------|---------------------------|--------|
| COND exhaustion → `()` | Returns **data** empty, not call to operator NIL | **pass** |
| `(atom '())` / EQ on empty | Needs empty **value**, not NIL opcode | **pass** |
| List terminator in CONS chains | Data `()` | **pass** |
| Host `NULL` / C null pointer as “NIL primitive” | Host null is a **different** carrier; if used as the only empty, may smuggle | **watch** |
| Surface function named `nil` bound to operator SID | Reintroduces NIL as operator under a name | **fail** if required |
| Treating predicate `0` as NIL | Collapses D1 with ground data | **fail** |

**Bounded conclusion:** H-NIL survives the obvious classical reconstructions **if** empty stays data and never becomes the operator table entry. It fails if the language requires a callable NIL root or equates NIL with bit `0`.

## Relation to pressure maps

| source | NIL pressure | use |
|--------|-------------:|-----|
| #2031 corpus | deps exist, exclusive 0 | prioritization only |
| #2035 pure graph | support 1 (self) | no generator family |
| this audit | capability = ground_value | **candidate to demote from operator seed** |

Low exclusive pressure does **not** prove H-NIL. The smuggling audit is the actual argument shape.

## Falsifiers that would kill H-NIL

1. A required corpus form whose only honest model is “invoke operator NIL”.
2. Proof that `()` cannot be data without an operator seed entry.
3. Blind WSM (wsm#12) producing a first distinction that forces NIL into the operator kernel.

## Upgrade path (only if all pass)

```text
conjecture H-NIL
  → witnesses on corpus without operator-NIL
  → #2018 row split: operator-bīja vs data-ground
  → owner review before any code map change
```

Until then: **bīja3 remains an 8-seed premise** including NIL.

## One-line summary

```text
Empty is data; calling it an operator may be historical packaging, not necessity.
```
