# Alternative basis probe H-COND (#2019)

**Agent:** grok-xai  
**Epistemic status:** **conjecture / negative on elimination**  
**Parent:** `2019-seed-necessity.md` · #1986 AND/OR falsifiers  
**Lock:** `111` COND stays in bīja3 **premise**; no code reassignment

## Question

```text
Is COND a necessary operator root, or can controlled branching
be recovered from predicates + other seeds alone?
```

## Capability at stake

```text
conditional_control:
  choose which subform to evaluate based on a test value
  (McCarthy conditional — not a Boolean lattice operator)
```

Distinct from D1 bits, from EQ/ATOM results, and from AND/OR *data* combinators.

## Candidate reconstructions

| candidate | idea | smuggles conditional_control? | verdict |
|-----------|------|-------------------------------|--------|
| **C1** host `if` / jump | CPU branch | **Host COND** | **smuggle** |
| **C2** Church-style Boolean encodings | `λt.λf. …` | Needs abstraction+application roots not in bīja3; different basis | **out of scope / not smaller** |
| **C3** AND/OR as `1110/1111` children of COND | specialize COND into lattice ops | **Falsified** under current `()≠0` / PredicateBit law (#1986) | **dead path** |
| **C4** only EQ/ATOM, no branch | compute predicates, always eval all arms | Loses short-circuit control; different semantics | **not equivalent** |
| **C5** COND as macro over nested EQ | expand to EQ chains | Expansion still needs a **branching** evaluator rule | **smuggle** |
| **C6** multi-values / exceptions as control | exotic | Not McCarthy conditional | **out of scope** |

## Important separation

```text
PredicateBit / D1     = what a test *means* (0/1)
COND                  = whether/which arm *runs*
AND/OR data ops       ≠ COND (and not earned as 111x children)
```

Falsifying AND/OR **children** does not remove COND **root** — same pattern as EQ generator vs EQ root.

## Bounded conclusion

```text
H-COND-0  "COND derivable from EQ/ATOM/CAR/CDR/CONS/QUOTE"
          → unsupported (branching authority reappears)

H-COND-1  "COND ≡ Boolean AND/OR"
          → false (control ≠ lattice); 111x path falsified

H-COND-2  "conditional_control is a distinct capability;
           packaging as 111 is historical;
           PredicateBit is the test domain, not a substitute for COND"
          → best fit
```

## Contrast (full high-priority set)

| probe | capability | eliminable? |
|-------|------------|-------------|
| H-NIL | ground data | maybe |
| H-QUOTE | eval suspend | no |
| H-EQ | leaf sameness | no |
| H-CONS | pair intro | no |
| **H-COND** | **branch control** | **no** |
| CAR/CDR | elim + generator | keep |

## Falsifiers for H-COND-0

1. Full corpus branching with no conditional authority (seed or host).  
2. Revival of 111x AND/OR without invalidating #1986 counterexamples.

## Non-actions

- no removal of `111`  
- no AND/OR allocation under COND  
- no production change  

## One-line summary

```text
Tests are not branches — COND stays the conditional_control root.
```
