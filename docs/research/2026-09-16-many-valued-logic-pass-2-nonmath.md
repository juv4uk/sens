# MANY-VALUED-RESEARCH-1 — Pass 2: non-mathematical reasoning only

Issue: #223  
Governing architecture: #222, #224, #225  
Branch: `research/223-many-valued-logic`  
Status: research evidence / NOT a ratified language contract  
Date: 2026-09-16

## Corrected scope

Mathematics is out of scope for this pass.

```text
()
  ↓
exact ℚ binary decisions
  ↓
mathematical result layer (#225)
  ↓
THIS PASS: non-mathematical many-valued reasoning
```

The target territory includes:

- incomplete knowledge;
- inconsistent/conflicting information;
- positive and negative support;
- ignorance vs contradiction;
- defaults and nonmonotonic reasoning;
- beliefs / knowledge / epistemic change;
- temporal reasoning;
- linguistic/semantic classification;
- vague predicates;
- uncertainty/probability when used as reasoning annotations about world claims;
- provenance / justification / source reliability;
- agent/world-model reasoning.

The lower layer may never redefine `()`, binary ℚ semantics, or mathematical result objects.

---

## Finding 1 — Belnap/FDE remains the minimal information-state kernel

Belnap/Dunn-style four-valued logic directly distinguishes:

```text
TRUE-ONLY
FALSE-ONLY
NEITHER
BOTH
```

This is valuable because it separates two cases that classical and many three-valued systems often conflate:

```text
lack of support  !=  contradictory support
```

It is both paraconsistent (conflict does not explode) and paracomplete (information gaps are representable).

Modern information-based logic literature still treats Belnap's core as a question-answering logic for possibly incomplete and inconsistent databases.

Leads:

- Melvin Fitting, *Logic Programming on a Topological Bilattice* (1988): generalized truth values as evidence for and against, possibly incomplete or contradictory. DOI: https://doi.org/10.3233/FI-1988-11206
- Ofer Arieli & Arnon Avron, *Reasoning with Logical Bilattices* (1996): proof systems and efficient inference from possibly inconsistent data. DOI: https://doi.org/10.1007/BF00215626
- Recent review of Belnap's computer-science influence: https://doi.org/10.1007/s11225-026-10230-3

Assessment:

- excellent minimal state algebra;
- not enough by itself for time, defaults, epistemic modalities, provenance or domain-specific annotations.

---

## Finding 2 — Bilattices are the strongest small algebraic chassis

A bilattice provides two distinct partial orders:

```text
truth order      — orientation toward truth/falsity
knowledge order  — amount/precision/consistency of information
```

This is architecturally important because my-lisp must not collapse "truth status" and "information amount" into one scalar.

Fitting's work uses generalized spaces of truth values in logic programming, and Arieli/Avron show bilattices can support paraconsistent inference over inconsistent data.

Bilattice-based epistemic logic has also been extended to reasoning about knowledge and changes in knowledge, showing that the bilattice idea can sit under modal/epistemic operators rather than replacing them.

Lead:

- *Bilattice logic of epistemic actions and knowledge* (2020): https://doi.org/10.1016/j.apal.2020.102790

Assessment:

- strongest candidate for a small core information algebra;
- should likely be treated as a substrate, not the whole language of non-mathematical reasoning.

---

## Finding 3 — Generalized Annotated Logic is a stronger umbrella candidate than one fixed truth table

The strongest new candidate in this pass is **Generalized Annotated Logic Programming (GAP/GALP)**.

Its key idea is that propositions carry annotations drawn from a lattice/semilattice instead of being restricted to one hard-coded truth domain.

Kifer/Subrahmanian's generalized annotated framework was explicitly developed for expert systems and uncertainty, and showed that multiple earlier multivalued logic-programming systems, Fitting's bilattice-based logic programming, and some temporal reasoning formalisms can be embedded in the same framework.

Primary lead:

- Michael Kifer & V. S. Subrahmanian, *Theory of generalized annotated logic programming and its applications*, Journal of Logic Programming 12(4), 1992. DOI: https://doi.org/10.1016/0743-1066(92)90007-P

Important consequence:

```text
one Lisp reasoning surface
        |
        +-- Belnap/bilattice annotations
        +-- temporal annotations
        +-- uncertainty annotations
        +-- domain-specific lattice annotations
```

rather than:

```text
one universal scalar truth value for everything
```

This is highly compatible with pyramid sovereignty because the annotation algebra can remain strictly local to the non-mathematical floor.

---

## Finding 4 — Annotated logic already has mature nonmonotonic extensions

For ordinary-world reasoning, defaults and defeasible conclusions matter. A purely monotonic many-valued algebra is insufficient.

Annotated nonmonotonic rule systems combine annotated logics with general nonmonotonic rule systems and explicitly present the result as a general-purpose nonmonotonic reasoning framework over arbitrary multiple-valued logics.

Lead:

- *Annotated nonmonotonic rule systems*, Theoretical Computer Science 171 (1997), 111–146. DOI: https://doi.org/10.1016/S0304-3975(96)00127-2

This is important for my-lisp because it suggests a separation:

```text
annotation/value algebra  !=  inference regime
```

The same underlying many-valued states may be consumed by monotonic, default, stable, or other reasoning semantics.

---

## Finding 5 — AFT is a candidate meta-semantics, not a truth algebra

Approximation Fixpoint Theory (AFT) provides a uniform algebraic account of several nonmonotonic semantics using lattice/bilattice approximations.

It associates approximating operators with Kripke–Kleene, stable and well-founded fixpoints and has direct logic-programming applications.

Primary lead:

- Marc Denecker, Victor Marek, Miroslaw Truszczynski, *Ultimate approximation and its application in nonmonotonic knowledge representation systems*, Information and Computation 192(1), 2004. DOI: https://doi.org/10.1016/j.ic.2004.02.004

Recent work also embeds justification theory into AFT, reinforcing the idea that AFT can unify semantics while separate justification/provenance structures explain why facts hold.

Lead:

- *Embedding justification theory in approximation fixpoint theory*, Artificial Intelligence 331 (2024), Article 104112. DOI: https://doi.org/10.1016/j.artint.2024.104112

Assessment:

- AFT is a strong candidate for the generic fixpoint/nonmonotonic engine;
- it should not become a universal truth-value set.

---

## Finding 6 — Generalized Annotated Logic has a modern executable descendant

PyReason is a current implementation based on generalized annotated logic. It supports open-world temporal reasoning, graph structures, explainable inference traces and several annotation styles including fuzzy/real-valued/interval forms.

Leads:

- Dyuman Aditya et al., *PyReason: Software for Open World Temporal Logic* (2023): https://arxiv.org/abs/2302.13482
- PyReason project: https://pyreason.syracuse.edu/
- 2025/2026 Lattice Annotated Temporal (LAT) logic work extends generalized annotated programs with temporal and open-world semantics: https://arxiv.org/abs/2509.02958

This is implementation evidence that a lattice-annotated architecture can remain extensible while supporting large knowledge graphs and temporal reasoning.

Important warning for my-lisp:

PyReason's use of real-valued intervals as logical annotations does **not** mean my-lisp should merge its mathematical-result layer with logic. In our pyramid such numerical annotations remain local metadata of the non-mathematical reasoning floor.

---

## Finding 7 — one fixed many-valued logic still looks too narrow

The non-mathematical territory contains qualitatively different phenomena:

```text
information gap
contradiction
source reliability
vagueness
probability/confidence
belief/knowledge
change over time
default assumptions
causal/agent state
provenance/justification
```

No evidence found so far supports collapsing all of these into one ordered scalar or one small fixed truth table.

The evidence instead points toward three separable layers **inside the non-mathematical floor**:

```text
A. information-state algebra
   Belnap / bilattice-style support-for and support-against

B. annotation/domain algebra
   generalized annotated logic / pluggable lattices

C. inference semantics
   monotonic fixpoint / AFT / stable / well-founded / default / temporal extensions
```

This does not add new floors above the many-valued floor. It is an internal decomposition of that floor.

---

## Current strongest architecture hypothesis — NOT RATIFIED

```text
                         ()
                          |
                 exact ℚ binary
                          |
                mathematical results
                          |
                          v
          NON-MATHEMATICAL REASONING FLOOR
                          |
             Generalized Annotated Logic
               (common proposition shell)
                          |
          +---------------+---------------+
          |                               |
   bilattice information             other domain
       annotations                    lattices
          |                               |
          +---------------+---------------+
                          |
                inference semantics
             AFT / stable / well-founded
             temporal / default / etc.
                          |
                          v
                         ()
```

Interpretation:

- **GAP/GALP** is currently the strongest candidate for the *common shell*;
- **Belnap/Fitting bilattice** is currently the strongest default/minimal information algebra;
- **AFT** is currently the strongest candidate for a generic nonmonotonic/fixpoint semantics layer;
- epistemic, temporal, fuzzy, probabilistic or domain-specific behavior should be extensions/annotation algebras, not new universal truth authorities.

---

## Sovereignty tests every candidate must pass

1. Removing the entire non-mathematical reasoning module leaves `()`, ℚ-binary and mathematical-result semantics unchanged.
2. Internal `NEITHER`, `BOTH`, intervals, confidences or annotations never become universal Lisp truth values.
3. An empty/no-result query remains `()` and is not silently mapped to a candidate logic's bottom element.
4. Mathematical values cannot be reclassified as logical annotations merely for implementation convenience.
5. Different annotation algebras must be locally explicit and composable.
6. Provenance/justification must survive inference instead of being erased into a scalar status.
7. Conflict must not explode into arbitrary conclusions.
8. Ignorance and contradiction must remain distinguishable.

---

## Next experiments

1. Encode Belnap FOUR as one annotation lattice inside a tiny generalized-annotated Lisp prototype.
2. Represent a fact with separate positive/negative evidence and provenance.
3. Add a second annotation algebra for source confidence without changing FOUR itself.
4. Run a backward-chaining query through both annotation spaces.
5. Compare monotonic fixpoint vs stable/well-founded/AFT-style behavior on a default rule.
6. Add temporal annotation to show that time does not require changing the base information algebra.
7. Verify that no result remains outer `()` rather than the lattice bottom.

## Current conclusion

Do **not** ratify one universal many-valued truth table yet.

The strongest evidence currently supports a **lattice-annotated family architecture**:

```text
Generalized Annotated Logic shell
        + Belnap/Fitting default information bilattice
        + pluggable domain lattices
        + AFT/nonmonotonic reasoning semantics
```

This is now the primary candidate to attack with executable my-lisp witnesses.