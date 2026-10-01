# Alternative basis probe H-CONS (#2019)

**Agent:** grok-xai  
**Epistemic status:** **conjecture / negative on elimination**  
**Parent:** `2019-seed-necessity.md`  
**Lock:** `100` CONS stays in bīja3 **premise**; no code reassignment

## Question

```text
Can CONS be dropped if CAR and CDR exist?
Is pair construction recoverable without an introduction form?
```

## Capability at stake

```text
pair_constructor:
  form a new pair from two values (introduction)
pair_destructor:
  CAR / CDR projections (elimination)
```

In a closed pair calculus, introduction and elimination are dual. Destructors alone do not build.

## Candidate reconstructions

| candidate | idea | smuggles constructor? | verdict |
|-----------|------|----------------------|--------|
| **C1** only CAR/CDR | project existing pairs | Cannot create pairs not already in the store | **incomplete** |
| **C2** host `malloc` + write fields | runtime allocates cells | **Host CONS** under another name | **smuggle** |
| **C3** quote of pre-built literals only | all pairs come from source text | No computed pairs; weaker language | **not equivalent** |
| **C4** CONS as macro over “pair” type | surface sugar | Still needs primitive allocation | **smuggle** |
| **C5** linear types / unique cells without CONS op | exotic capability | Not McCarthy basis; out of scope | **out of scope** |
| **C6** fuse CONS into QUOTE | quoted structure only | Loses `(cons (f x) y)` computed construction | **not equivalent** |

## Duality with CAR/CDR

```text
CONS  : A × A → Pair     introduction
CAR   : Pair → A         elimination
CDR   : Pair → A         elimination
```

Local **suffix generator** on CAR/CDR (append bit = compose projections) does **not** invent introduction. Generator economy that favors CAR/CDR families therefore **strengthens** keeping CONS as the matching root, not deleting it.

## Bounded conclusion

```text
H-CONS-0  "CONS derivable from CAR/CDR alone"     → unsupported
H-CONS-1  "CONS only host allocation"           → smuggle / wrong layer
H-CONS-2  "pair_constructor is dual capability;
           packaging as 100 is historical;
           cannot close list calculus without it" → best fit
```

## Contrast

| probe | role | eliminable? |
|-------|------|-------------|
| H-NIL | ground data | maybe |
| H-QUOTE | eval control | no |
| H-EQ | leaf sameness | no |
| **H-CONS** | **introduction** | **no** |
| CAR/CDR | elimination + generator | keep |

## Falsifiers for H-CONS-0

1. Corpus of computed lists with no pair-introduction authority (seed or host).  
2. Proof that CAR/CDR generate new pairs (they do not).

## Non-actions

- no removal of `100`  
- no “CONS children” generator claim without separate evidence (#2017-style)  
- no production change  

## One-line summary

```text
Destructors do not construct — CONS stays the introduction root.
```
