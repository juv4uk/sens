# Alternative basis probe H-ATOM (#2019)

**Agent:** grok-xai  
**Epistemic status:** **conjecture / weak-negative on elimination**  
**Parent:** `2019-seed-necessity.md` · H-EQ  
**Lock:** `010` ATOM stays in bīja3 **premise**; no code reassignment

## Question

```text
Is ATOM a necessary operator root, or is “atom vs pair”
recoverable from EQ, structure, or host tags alone?
```

## Capability at stake

```text
type_predicate:
  unary test — is this value an atom (non-pair) or a pair?
```

Distinct from **identity_predicate** (EQ, binary sameness) and from **pair destructors** (CAR/CDR, which presuppose pair).

## Candidate reconstructions

| candidate | idea | smuggles type test? | verdict |
|-----------|------|---------------------|--------|
| **C1** try CAR/CDR and catch failure | “if car fails → atom” | Exception/failure is a **control** channel; host type tag | **smuggle** |
| **C2** EQ against a set of known atoms | only works for finite closed atom set | Incomplete for open atom domains | **not equivalent** |
| **C3** host tag bit / discriminant | runtime type tag | **Host ATOM** | **smuggle** |
| **C4** unify with EQ | EQ is binary; ATOM is unary partition | Category error (see H-EQ C6) | **fail** |
| **C5** only pairs exist; no atoms | everything is pair/encoding | Different language (no symbols/numbers as atoms) | **not equivalent** |
| **C6** ATOM as `not (pair?)` with pair? primitive | renames the same unary partition | Still a type_predicate root | **not eliminated** |

## Economy note

ATOM→NULL style one-off generators fail the economy bar (#1973). That argues against **children** of ATOM, not against ATOM as a **root** type test.

## Bounded conclusion

```text
H-ATOM-0  "ATOM derivable from EQ/CAR/CDR/CONS alone"
          → unsupported (unary partition reappears as host/exception)

H-ATOM-1  "ATOM ≡ EQ"
          → category error

H-ATOM-2  "type_predicate is distinct from identity_predicate;
           packaging as 010 is historical;
           may be spelled pair?/atom? but not deleted in a pair+atom ontology"
          → best fit
```

## Full seed scoreboard (packaging probes complete)

| seed | probe | eliminable? |
|------|-------|-------------|
| 000 NIL | H-NIL | **maybe** (data) |
| 001 QUOTE | H-QUOTE | **no** |
| **010 ATOM** | **H-ATOM** | **no** |
| 011 EQ | H-EQ | **no** |
| 100 CONS | H-CONS | **no** |
| 101/110 | matrix | **keep** |
| 111 COND | H-COND | **no** |

## Falsifiers for H-ATOM-0

1. Pair+atom corpus with no unary type partition (seed or host discriminant).  
2. Proof that EQ alone induces atom/pair split without tags.

## Non-actions

- no removal of `010`  
- no ATOM suffix-generator  
- no production change  

## One-line summary

```text
Sameness is not a type partition — ATOM stays the unary type root.
```
