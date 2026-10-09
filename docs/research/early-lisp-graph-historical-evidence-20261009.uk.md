# Early Lisp graph research — archival evidence, current D3 crosswalk

**Status:** research archive only. This is not a semantic registry, D1–D9 coordinate proposal, or D10 admission list.

## Why this selective archive exists

The old branch research/1962-lisp1-15-domain-graph is four unique commits ahead of main but more than a thousand commits behind it. Its valuable contribution is the typed graph of early-Lisp dependencies and its counterexamples to overly strong code-allocation claims. Its node file also embeds a pre-pivot seed assignment: EQ=011, CONS=100, CAR=101, CDR=110, COND=111. That assignment does not match current ratified D3.

Current canonical D3, from lib/domains/d3.lisp, is: 000=(), 001=QUOTE, 010=ATOM, 011=CDR, 100=CAR, 101=EQ, 110=COND, 111=CONS. The old codes are kept only under historical_snapshot; the current crosswalk is a separate field.

## Preserved material

The machine-readable archive includes 34 nodes, 129 graph edges, 10 bounded falsification records, three observational-equivalence cases, 16 bīja3 dependency-pressure records, and four selector-relation-kernel comparisons. Old nodes/relations are evidence and diagnostic inputs, not semantic candidates. Every row carries coordinate=null, selected_d10_candidate=false, ratified=false.

## Main scientific value for D10 review

The falsification ledger preserves important scoped counterexamples:
- A Hamming-1 hypercube cannot encode every strong relation because the bounded seed relation contains a triangle.
- Unordered direct support cannot select a unique ordered prefix parent: CADR and CDAR share the same unordered support while their selector order differs.
- Named helper depth changes under refactoring and is not a stable semantic rank.
- Transitive seed support alone cannot identify a meaning: APPEND and PAIR can share support while their operations differ.
- LISP I and LISP 1.5 evaluator strongly-connected-component topologies differ, so evaluator SCC is not placement authority.

These are useful negative tests against unjustified D10 allocation. They do not prove no future code family is possible; each claim keeps its original scope and falsifier.

## Primary sources

The 1960 McCarthy paper describes the S-expression and recursive S-function basis of early Lisp; compare it with the 1962 LISP 1.5 Programmer's Manual and the Computer History Museum's LISP archive:
- [McCarthy 1960 paper scan](https://www.cs.cmu.edu/~crary/819-f09/McCarthy60.pdf)
- [LISP 1.5 Programmer's Manual scan](https://www.bitsavers.org/pdf/mit/rle_lisp/McCarthy_LISP_1.5_Programmers_Manual_2ed_1985.pdf)
- [Computer History Museum LISP History Collection](https://softwarepreservation.computerhistory.org/LISP/)

The archival validator pins current authority hashes, checks the corrected D3 crosswalk, preserves old codes only as history, and rejects any attempt to promote a row to a current coordinate, D10 selection, or ratification.
