# MANY-VALUED-RESEARCH-1 — Pass 1

Issue: #223  
Governing architecture: #222, #216, #224  
Branch: `research/223-many-valued-logic`  
Status: research evidence / NOT a ratified language contract  
Date: 2026-09-16

## Research paradigm

The upper floors are already fixed and are not candidates for redesign:

```text
()
whole answer/no-answer possibility space
        |
        v
exact rational mathematics only (ℚ)
        |
        +-- exact NO  -> 0/1
        `-- exact YES -> 1/1
        |
        v
richer logic territory
= all non-ℚ mathematics
+ all non-mathematical questions
```

A lower logic may refine only delegated territory. It may not redefine `()`, `0/1`, `1/1`, or the ℚ boundary.

## Pass-1 question

Do existing many-valued / non-classical systems provide one principled algebra for the entire delegated territory, or do we need a family of lower logics under a common interface?

## Finding 1 — bilattices are much more general than Belnap FOUR

Melvin Fitting's 1991 work is the strongest foundational lead so far. It treats a bilattice as a generalized truth/information space for logic programming. The framework is not limited to the four Belnap states: the paper explicitly discusses bilattices based on finite many-valued logics and probabilistic-valued logic as well as Belnap's four-valued case.

This matters for my-lisp because a bilattice can act as an algebraic *chassis* for lower reasoning domains rather than as one fixed four-value enum.

Primary lead:

- Melvin Fitting, **Bilattices and the semantics of logic programming**, Journal of Logic Programming 11(2), 1991.
  - DOI: https://doi.org/10.1016/0743-1066(91)90014-G
  - OpenAlex: https://openalex.org/W2001805670

Important interpretation:

```text
truth order      = orientation with respect to truth/falsity
knowledge order  = amount / precision / consistency of information
```

This two-order separation is highly compatible with our rule that knowledge state must not be confused with the upper binary layer.

## Finding 2 — bilattice research already separates truth values from information about truth values

Later work explicitly embeds an underlying many-valued algebra V into a bilattice B and interprets bilattice elements as *pieces of information about* the truth values in V rather than as the truth values themselves.

Lead:

- **Bilattices for deductions in multi-valued logic**, International Journal of Approximate Reasoning 54(8), 2013.
  - https://doi.org/10.1016/j.ijar.2013.04.004

This is especially relevant to our sovereignty rule:

```text
upper mathematical object/value
        !=
lower information state about that object/value
```

It suggests that richer logic can describe evidence, approximation, conflict, support, or uncertainty *about* a non-ℚ mathematical value without replacing the value itself.

## Finding 3 — non-ℚ mathematics should not be reduced to fuzzy truth degrees

The exact-real / constructive-computation literature gives a strong warning against treating an irrational number itself as a many-valued truth.

Continuous-domain and exact-real work represents real numbers by computational objects / approximations whose precision can improve, not by replacing the number with a truth degree.

Leads:

- **A constructive theory of continuous domains suitable for implementation**, Annals of Pure and Applied Logic 159(3), 2009. The work develops continuous domains and applies them to interval domains and exact real numbers.
  - https://doi.org/10.1016/j.apal.2008.09.025

- **A domain-theoretic approach to computability on the real line**, Theoretical Computer Science 210(1), 1999.
  - https://doi.org/10.1016/S0304-3975(98)00097-8

Architectural consequence for my-lisp:

```text
pi / sqrt(2) / exact-real object
        = mathematical data

status of a proposition about it
        = richer-logic result
```

For example, richer logic might return a proof object, interval enclosure, unresolved comparison, or support state about `pi > 3`; it should not turn `pi` itself into `0.7` or `NEITHER`.

## Finding 4 — exact real equality / trichotomy is not generally decidable constructively

Constructive and computable analysis provide an important reason why the non-ℚ floor cannot simply be a disguised binary floor.

For general exact/computable reals, equality is not decidable in the ordinary algorithmic sense; full real-number trichotomy is also not constructively available in general.

This fits the pyramid naturally:

```text
exact ℚ comparison
    -> upper binary layer can answer 0/1 or 1/1

general exact real comparison
    -> may yield proof / refutation / interval separation / unresolved state
    -> richer logic territory
    -> if no defined answer is produced: ()
```

Research leads:

- Constructive mathematics literature on failure of general real trichotomy.
- Exact-real computation literature on undecidability of equality tests.

This is not evidence that all non-ℚ propositions are undecidable; it is evidence that we must preserve explicit proof/decision state instead of forcing universal yes/no.

## Finding 5 — Belnap/FDE remains an excellent minimal information kernel, but not a complete lower universe

Belnap-Dunn gives four independent support states:

```text
TRUE-ONLY   = support P, no support not-P
FALSE-ONLY  = support not-P, no support P
NEITHER     = support neither side
BOTH        = support both sides
```

The pair representation remains attractive:

```text
(pos-support, neg-support)
(0,0) -> NEITHER
(1,0) -> TRUE-ONLY
(0,1) -> FALSE-ONLY
(1,1) -> BOTH
```

Strengths:

- distinguishes information gaps from conflicts;
- paraconsistent: conflict need not explode;
- fits proof/provenance attached independently to positive and negative support;
- has direct logic-programming descendants.

Limitation exposed by our new paradigm:

- FOUR alone does not represent exact-real numeric objects, interval enclosures, fuzzy degree, probability, or arbitrary domain-specific result algebras.

Therefore FOUR is currently best viewed as a minimal information-state kernel / test baseline, not yet as the whole richer layer.

## Finding 6 — fuzzy bilattice work shows a path to graded gaps and gluts

Recent work extends Belnap-Dunn-style bilattice semantics to `[0,1]^2`, where the two coordinates independently represent degree of truth and degree of falsity. This allows partial gaps and partial gluts instead of only four crisp corners.

Lead:

- Libor Běhounek, Martina Daňková, Antonín Dvořák, **Free Quantification in Four-Valued and Fuzzy Bilattice-Valued Logics**, 2023.
  - arXiv: https://arxiv.org/abs/2306.13079

Potential value for my-lisp:

```text
(alpha, beta)
alpha = support/degree for P
beta  = support/degree for not-P
```

Risk:

- `[0,1]` must remain a lower delegated algebra only.
- It must not reinterpret upper `0/1` and `1/1` as universal fuzzy truth constants.
- Vagueness/graded support must remain distinct from mathematical rational binary truth.

## Finding 7 — multi-adjoint logic programming supports a family-of-logics architecture

Multi-adjoint logic programming is relevant not because we should copy its fuzzy semantics, but because it demonstrates a mature framework in which different implication/conjunction pairs can coexist over a lattice-valued semantics.

Leads:

- Jesús Medina, Manuel Ojeda-Aciego, Peter Vojtáš, work on multi-adjoint logic programming and completeness.
- Multi-adjoint frameworks generalize monotonic/residuated/fuzzy/possibilistic styles and allow multiple inference operators.

Architectural lesson:

```text
one language
    |
    +-- logic algebra A
    +-- logic algebra B
    +-- logic algebra C

rather than

one universal truth scale forced on every domain
```

This is currently a strong argument for option C from #223: a family of explicit delegated logic domains under a common language-owned interface.

## Finding 8 — Approximation Fixpoint Theory may be the semantic engine above individual lower algebras

Approximation Fixpoint Theory (AFT) generalizes fixpoint semantics using lattices/bilattices and unifies several well-known semantics for nonmonotonic reasoning.

Leads:

- Denecker / Marek / Truszczynski line of AFT work.
- **Ultimate approximation and its application in nonmonotonic knowledge representation systems**, Information and Computation 192(1), 2004.
  - https://doi.org/10.1016/j.ic.2004.02.004

- Current AFT work continues to generalize logic-programming and knowledge-representation semantics, including non-deterministic and weak-bilattice settings.

Possible role in my-lisp:

```text
bilattice / lattice = answer-information algebra
AFT                 = generic fixpoint semantics for reasoning over it
```

AFT is therefore not itself a candidate truth-value set; it is a candidate *reasoning meta-framework*.

## Finding 9 — one universal lower truth scale is currently not supported by the evidence

The literature separates at least these phenomena:

```text
exact real representation
interval/approximation precision
positive/negative evidence
conflict
lack of evidence
vagueness
probability
nonmonotonic default reasoning
proof/provenance
```

Existing mature systems often combine some of them, but they do not justify treating all of them as one scalar truth degree.

Current evidence therefore favors:

```text
                    ()
                     |
                     v
              exact ℚ binary
               0/1 | 1/1
                     |
                     v
           delegated richer router
          /          |          \
         /           |           \
 non-ℚ math     evidence/KR    domain degree
 exact-real     bilattice/AFT  fuzzy/prob/etc.
 interval       proof/support  only when apt
 symbolic
```

This is a *research hypothesis*, not yet architecture.

## Candidate architecture after Pass 1 — NOT RATIFIED

A promising minimum is:

1. Keep mathematical values as mathematical data.
2. Add a language-owned `result/evidence` protocol for the richer territory.
3. Use a Belnap-style independent positive/negative support projection as the smallest contradiction/gap kernel.
4. Permit domain algebras (exact-real enclosure, fuzzy, probability, etc.) to attach their own values without becoming universal truth.
5. Use bilattice-compatible ordering when the domain has both truth/support and information/precision dimensions.
6. Investigate AFT for fixed-point semantics of `reason` / nonmonotonic programs.
7. Preserve `()` outside all these algebras as the zero/no-answer result.

## Falsification tests for the next pass

Any proposed richer framework must fail if it requires one of these:

```text
() == NEITHER/UNKNOWN
0/1 or 1/1 reinterpreted by the lower algebra
pi or sqrt(2) replaced by truth degrees instead of represented as math data
probability == truth support
fuzzy degree == ignorance
conflict collapses to false
lack of evidence collapses to false
lower logic changes upper control semantics
```

## Next research pass

1. Read Fitting 1991 operations and fixed-point construction closely.
2. Extract the exact product/bilattice representation theorem relevant to arbitrary underlying lattices.
3. Compare Belnap FOUR, fuzzy bilattice `[0,1]^2`, and a candidate interval/evidence bilattice using the same four test propositions.
4. Study constructive/exact-real result forms for `pi`, `sqrt(2)`, equality, `<`, and interval separation.
5. Compare AFT vs direct Fitting semantics for `lib/reason.lisp`.
6. Inspect multi-adjoint logic programming as evidence for multiple coexisting lower algebras.
7. Build a Lisp-authored research prototype that represents support/evidence as ordinary data without relying on global truthiness.

## Current research conclusion

No many-valued logic has been selected.

The strongest current synthesis is:

> **Bilattice/Fitting is the leading general information/reasoning chassis, but non-ℚ mathematical values should remain exact/symbolic/interval mathematical objects. Richer logic should describe what is known, proved, approximated, contradicted, or unresolved about them. The evidence currently favors a family of delegated lower algebras rather than one universal many-valued truth scale.**
