# Alternative basis H-NIL (#2019)

**Agent:** grok-xai  
**Epistemic status:** **conjecture + bounded current-corpus witness** (not theorem, not production)  
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

## Current-corpus kill test — 2026-10-01

A reproducible witness now attacks the strongest immediate falsifier: does the
**current executable SENS corpus** require empty/NIL as a callable operator?

Exact witness:

```text
main baseline                     a56f570ada09…
active NIL tokens in lib/*.lisp   54
callable NIL/nil list heads       0
00000000 executable heads         0
00000000 non-metadata lib tokens  0
00000000 evaluator SID route      absent
00000000 mechanism row            absent
Contract 10 ground separation     present
```

The 54 surviving `NIL` tokens are data/history uses, chiefly Core1 values,
arguments, terminators and comparison subjects. They are **not** `(NIL ...)`
operator calls. The lexer discards comments and strings before classifying list
heads, so prose does not count as executable evidence.

The second, independent signal is runtime shape: current evaluator route metadata
starts at `00000001`, while structural `()` evaluates as its own empty value.
Contract 10 also explicitly states that current Function8 `00000000` is not the
empty-list value.

This does **not** prove that the all-zero function slot can never hold an
independent function. It proves only the H-NIL claim in the bounded current
system: **ground data does not currently need callable/operator NIL authority**.
If `00000000` later gains an unrelated function, that is a new function-role
question, not evidence that structural empty has become an operator again.

Executable evidence: `experiments/research-2019-h-nil-corpus.py` and the
`H-NIL corpus witness` workflow.

**Status consequence:** H-NIL remains a conjecture globally, but it now has an
executable bounded witness over the current corpus. The next upgrade gate is the
blind WSM comparison / stronger formal derivation, not another packaging essay.

## Falsifiers that would kill H-NIL

1. A required corpus form whose only honest model is “invoke operator NIL”.
2. Proof that `()` cannot be data without an operator seed entry.
3. Blind WSM (wsm#12) producing a first distinction that forces NIL into the operator kernel.

## Upgrade path (only if all pass)

```text
conjecture H-NIL
  → bounded current-corpus witness ✓
  → blind/formal independent evidence
  → #2018 row split: operator-bīja vs data-ground
  → owner review before any code map change
```

Until then: **bīja3 remains an 8-seed premise** including NIL.

## One-line summary

```text
Empty is data; calling it an operator may be historical packaging, not necessity.
```
