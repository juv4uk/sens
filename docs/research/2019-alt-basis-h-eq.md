# Alternative basis probe H-EQ (#2019)

**Agent:** grok-xai  
**Epistemic status:** **conjecture / negative-leaning on elimination**  
**Parent:** `2019-seed-necessity.md`  
**Lock:** `011` EQ stays in bīja3 **premise**; no code reassignment

## Question

```text
Is EQ a necessary operator root, or can identity be recovered
from structure (CAR/CDR/CONS) and ATOM alone?
```

## Capability at stake

```text
identity_predicate:
  answer whether two values are the same on the atomic domain
  (and, with recursion, whether two trees are structurally equal)
```

Tree equality is not free from pair structure alone: leaves still need a sameness test.

## Candidate reconstructions

| candidate | idea | smuggles identity? | verdict |
|-----------|------|--------------------|--------|
| **C1** pointer / host identity | `==` on machine addresses | Host identity ≠ SENS semantic EQ domain | **smuggle / wrong theory** |
| **C2** only ATOM + structure | walk pairs; atoms compared by…? | Stops at leaves with no comparison | **incomplete** |
| **C3** encode atoms as unique CONS shapes | each atom a distinct tree shape | Requires infinite/host injection of shapes; renames atom table | **smuggle** |
| **C4** string/byte equality as primitive | move EQ into Text/Number domain ops | Still an **identity_predicate** root, relocated | **not eliminated** |
| **C5** EQ only on `()` and `t` | two-point domain | Weaker language; corpus needs more | **not equivalent** |
| **C6** unify EQ with ATOM | ATOM is unary type test, not binary sameness | Different arity and meaning | **category error** |

## Relation to #2017 / generator work

Selector-strength **children of EQ** (immediate prefix family like CAR/CDR) are already constrained/falsified as a *generator* pattern. That does **not** remove EQ itself — it blocks “EQ grows a suffix algebra the way CAR does”.

## Bounded conclusion

```text
H-EQ-0  "EQ derivable from CAR/CDR/CONS/ATOM/QUOTE/COND alone"
        → unsupported (leaf sameness always reappears)

H-EQ-1  "EQ only needed as host pointer equality"
        → wrong theory for SENS exact atoms / PredicateBit path

H-EQ-2  "identity_predicate is a distinct capability;
         packaging as 011 is historical; domain may widen (Text/Number)
         but the capability does not vanish"
        → best fit
```

## Contrast

| probe | eliminable? | packaging open? |
|-------|-------------|-----------------|
| H-NIL | maybe (data vs operator) | yes |
| H-QUOTE | no (eval model) | seed vs phase |
| **H-EQ** | **no** (leaf sameness) | domain extent / opcode |

## Falsifiers that would revive H-EQ-0

1. Full corpus equality without any binary sameness primitive (including host).  
2. Formal proof that ATOM+structure decides leaf identity (needs a leaf law).

## Non-actions

- no deletion of `011` from premise seed  
- no EQ suffix-generator allocation  
- no merge of EQ into ATOM  

## One-line summary

```text
Structure walks to leaves; leaves still need sameness — EQ stays a root capability.
```
