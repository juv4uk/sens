# Richer-logic domain boundary

Issue: #224  
Research parent: #223  
Governing pyramid: #222  
Binary contract: #216  
Branch: `research/223-many-valued-logic`  
Date: 2026-09-16

## Owner decision

The logical territory is partitioned by the rational boundary.

```text
                         ()
        whole possibility / zero-answer boundary
                         |
                         v
             exact rational mathematics ℚ
                   0/1 | 1/1
                  NO     YES
                         |
                         v
               richer logic territory
       non-ℚ mathematics + everything else
                         |
                         v
             no defined richer answer
                         |
                         v
                         ()
```

## Exact domain partition

### Floor 1 — absolute binary logic

This floor owns only mathematical questions whose essential values can be established exactly in ℚ.

Its complete logical output set is:

```text
0/1 = exact NO
1/1 = exact YES
```

It has no authority over any value or question that is not exactly rational mathematics.

### Floor 2 — richer / many-valued logic territory

This floor receives everything outside that exact ℚ domain.

It therefore includes two exhaustive classes:

```text
A. mathematics with non-rational result/content
B. all non-mathematical questions
```

Examples for A include:

- irrational values such as `sqrt(2)`;
- transcendental values such as `pi`;
- exact algebraic non-rationals;
- symbolic mathematical results that do not normalize exactly to ℚ;
- interval / approximation / numerical-analysis results;
- mathematical uncertainty or incompleteness that cannot honestly be reduced to the exact ℚ binary floor.

Examples for B include:

- Lisp structure/type/identity questions;
- knowledge, evidence, proof and provenance;
- incomplete knowledge;
- conflict / contradiction;
- language and semantic interpretation;
- fuzzy/vague classification;
- probability and uncertainty where appropriate;
- agent/world-model reasoning;
- any other non-mathematical question.

## Important: “richer logic” is a territory, not yet one algebra

This decision does NOT yet choose one universal many-valued logic for all of the lower territory.

The research question in #223 remains open:

```text
one fixed many-valued logic?
Belnap/Fitting bilattice core?
several explicit domain logics?
another established algebra?
```

What is now fixed is only the jurisdiction boundary:

```text
exact ℚ math -> binary
anything else -> richer logic territory
```

## Sovereignty law

The richer floor is subordinate to the upper floors.

It MAY:

- classify non-ℚ mathematics;
- represent several possible/partial/conflicting results;
- attach proofs, provenance, confidence, intervals, probabilities or fuzzy degrees where the selected domain logic warrants them;
- choose among established lower-domain logics.

It MUST NOT:

- redefine `()`;
- reinterpret `0/1` or `1/1`;
- expand binary authority beyond exact ℚ;
- force its own internal values into the binary floor;
- change the meaning of an already-established upper-floor answer;
- make one lower algebra the universal truth semantics of the whole language without a new explicit architecture decision.

## Routing law

Conceptually:

```text
question
   |
   +-- exact rational mathematics?
   |       |
   |       +-- yes -> binary floor -> 0/1 or 1/1
   |       |
   |       `-- no  -> richer territory
   |
   `-- non-mathematical -> richer territory

richer territory
   |
   +-- selected logic has a defined answer -> return that answer
   |
   `-- no defined answer -> ()
```

The routing decision itself must not fabricate a truth value.

## Research consequences for #223

Candidate logics must now be tested on BOTH of these classes, not only knowledge reasoning:

1. non-rational mathematics;
2. non-mathematical reasoning.

Required comparison questions:

- Can the candidate represent exact irrational/symbolic mathematical results without pretending they are rational binary values?
- Can it represent interval or approximate results without confusing approximation with epistemic ignorance?
- Can it represent incomplete and contradictory knowledge separately?
- Can it coexist with fuzzy/probabilistic subdomains without collapsing them into one scale?
- Can it leave the upper `()` and ℚ-binary floors untouched?
- Can several lower-domain logics coexist if one algebra is not semantically justified for every non-ℚ/non-mathematical problem?

## Witness targets

```text
(= 1/3 2/6)
    -> 1/1          ; exact ℚ binary

question essentially about pi
    -> lower richer-logic territory, never direct binary

question essentially about sqrt(2)
    -> lower richer-logic territory

structural Lisp question
    -> lower richer/structural result

knowledge/proof query
    -> lower richer result

no selected lower logic can establish an answer
    -> ()
```

## Architectural summary

```text
()  owns the whole possibility/no-answer boundary
 |
 +-- exact rational mathematics ℚ
 |      -> absolute 0/1 | 1/1
 |
 `-- everything outside that domain
        -> richer / many-valued territory
        -> domain-appropriate result
        -> or () when no answer exists
```

## Principle

**Binary logic owns only exact rational mathematics. Richer logic owns non-rational mathematics and everything non-mathematical, but may never impose its semantics upward.**
