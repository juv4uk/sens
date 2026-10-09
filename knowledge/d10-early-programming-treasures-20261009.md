# D10 historical-programming treasures — research queue (2026-10-09)

**Status:** hypothesis queue only. No candidate is selected, no inventory row is added, and no coordinate or ratification is granted by this document. D10 remains research-unratified.

## Why look this far back?

Early programming languages were not only collections of syntax. Lisp and early AI languages explored how symbolic expressions could be data, executable procedures, logical claims, proof attempts, and problem-solving control. Some ideas later became hidden inside runtimes or libraries. The research task is to recover the *observable law*, not to import a historical name or implementation detail.

### Primary historical sources

1. John McCarthy, **“Recursive Functions of Symbolic Expressions and Their Computation by Machine”** (MIT AI Memo 8, 1959; later CACM 1960). The 1960 paper says Lisp was motivated by the Advice Taker and formalized symbolic expressions / S-functions, including the universal `apply` as interpreter.  
   - MIT DSpace primary record: https://dspace.mit.edu/entities/publication/b66ae9e2-cc26-4735-a4b7-02cfbe6b0ce6
   - Readable paper copy: https://www.cs.cmu.edu/~crary/819-f09/McCarthy60.pdf
2. Carl Hewitt, **“Procedural Embedding of Knowledge in Planner”** (IJCAI 1971). Planner's research focus was the relationship between knowledge and the procedures invoked when that knowledge is relevant.  
   - Paper: https://citeseerx.ist.psu.edu/document?doi=a761f26f8239acd88fc83787f28a7f2d2ff9ea22&repid=rep1&type=pdf
   - MIT AI Memo 250, *Planner Implementation Proposal to ARPA* (1971): https://dspace.mit.edu/entities/publication/41d5d4f5-70c2-417c-9328-cde7b158b2b2
3. Hewitt, **“How to Use What You Know”** (IJCAI 1975) compares Planner-like problem-solving formalisms and discusses procedural/declarative knowledge.  
   - https://www.ijcai.org/Proceedings/75/Papers/026.pdf

These are donor leads, not automatic D10 admissions.

## Historical treasure matrix

| Historical idea | Potential language-visible law to investigate | Known overlap / risk | Current disposition |
|---|---|---|---|
| Advice Taker: declarative facts plus imperative knowledge | A query can derive an answer from explicit assertions and rules, while retaining why/how it was derived | SENS already has claims/evidence, proof, narration and knowledge-goal families. “Advice Taker” as a label adds nothing | **AUDIT EXISTING ROOTS** |
| Lisp S-expressions and universal `apply` | A finite symbolic expression can be interpreted by a language-defined evaluator independent of host representation | SENS/my-lisp already has evaluator, APPLY/invoke and substrate-witness architecture; likely heavily covered | **DUPLICATE ATTACK FIRST** |
| Planner procedural embedding / pattern-directed invocation | Matching a goal/pattern may select a procedure or rule whose execution is relevant to that goal | Overlaps existing rule matching, `PROVE-RULE`, forward firing and island dispatch. Must distinguish logical matching from procedure dispatch | **HIGH-VALUE AUDIT, NOT YET A CANDIDATE** |
| Failure-directed reasoning / backtracking | Failure of one attempted proof branch resumes a prior choice point while preserving the specified answer order and state | Existing Prolog island and proof-state logic may already cover it; host stack unwinding is not the semantic law | **HOLD UNTIL MINIMAL WITNESS** |
| Means-ends analysis / goal regression | Given a goal and operators with preconditions/effects, derive subgoals that could reduce the difference to a state | Could be ordinary composition over existing goals, rules and state transitions; requires a source-backed minimal irreducible example | **HOLD / DERIVABILITY ATTACK** |
| Assumption retraction / truth maintenance | Retracting a support invalidates exactly the conclusions whose justification depends on it, while preserving independently supported conclusions | Claim/evidence/provenance and JTMS/forward-rule families already exist. The unique law, if any, is dependency-sensitive retraction, not generic deletion | **COMPARE WITH EXISTING JTMS ROOTS** |
| Lisp property lists / symbol properties | Associate multiple keyed properties with a symbol and specify replacement, removal, absent-key and identity behavior | Likely derivable from maps plus symbol identity; host symbol plist layout is implementation detail | **LIKELY PROJECTION; PROVE OR FALSIFY** |
| Incremental definition and redefinition | A definition change affects subsequent lookup/evaluation according to explicit environment and binding rules, without retroactively changing captured lexical bindings unless specified | Current evaluator harvest includes `ENV-LOOKUP`, lambda/closure and group-recursion rows | **AUDIT CURRENT EVALUATOR CONTRACT** |
| Interactive correction / DWIM-style recovery | Produce a bounded set of explicit correction candidates while preserving the original input and exposing ambiguity rather than silently rewriting intent | Risk of UI-only fuzzy correction; may be a language-visible relation if deterministic, inspectable and non-mutating | **HOLD; REQUIRE GENERIC LAW** |
| Incremental compilation / interpreted-compiled coexistence | A function can be replaced or compiled while preserving the defined language-level identity and call behavior | Compiler/backend details are mechanisms unless observable identity, redefinition, or staging laws differ | **MECHANISM-ONLY UNTIL PROVEN OTHERWISE** |

## Concrete investigation order

### 1. First: procedural embedding versus ordinary rule matching

Use Planner as a historical conceptual donor, then pin an actual implementation or primary-source passage for the exact behavior. Compare it with the current SENS inventory's `PROVE-RULE`, `PROVE-GOAL-STATE`, `FIRE-RULE-MULTI`, `FIRE-RULES-MULTI`, knowledge-goal validation, and island invocation family.

Required minimal witnesses:
- Positive A: a goal matches a rule and triggers a declared procedure.
- Positive B: two applicable procedures are distinguished by an explicit, deterministic language rule.
- Falsifier: merely moving the same matching and dispatch into a different host runtime does not change the result.
- Negative controls: no matching goal; ambiguous matches; procedure failure; a procedure with a side effect must not be confused with a logical proof.

If existing rule matching plus invocation fully expresses the behavior, record **DERIVED** and stop. Do not add a new candidate.

### 2. Second: dependency-sensitive retraction

Compare early truth-maintenance ideas with existing SENS claim/evidence/provenance and forward-JTMS harvest. The candidate law would need to say exactly which conclusions survive when one support is removed. Ordinary `REMOVE`, deleting a record, or recomputing everything from scratch is not evidence of an independent root.

Required witnesses:
- A conclusion supported by two independent justifications survives removal of one.
- A conclusion with only one justification disappears after that justification is removed.
- A cyclic or mutually supporting dependency case has an explicitly specified result rather than host-order accidents.

If this is already an existing JTMS law, extend its evidence instead of minting another name.

### 3. Third: failure-directed control and goal regression

Investigate only after the first two lanes. Specify observable choice-point, answer-order, state-restoration and termination behavior; distinguish it from Prolog's implementation mechanism. For goal regression, give explicit state, action preconditions/effects, target goal and a counterexample showing why ordinary composition is insufficient.

## Admission gate

Before any new candidate can be proposed:
1. Pin donor repository commit, file path and exact function/paragraph/line.
2. State arity, input shape, output shape, ordering, mutation, failure and error behavior.
3. Give two positive witnesses and at least one falsifier / negative control.
4. Deduplicate against the *current pinned* D1–D9 and all current D10 semantic laws, not just names.
5. Attack derivability from existing operators and identify whether the proposal is merely I/O, compiler, runtime, ABI, UI or backend mechanism.
6. If still independent, route through #4463 and the canonical selection→ledger workflow (#4894/#4471). Any accepted research candidate remains unplaced and unratified until the owner decides otherwise.

## Scope and coordination

- Historical Lisp / metacircular evaluation: #4182 and the existing self-host harvest; avoid duplicating #4981.
- Chess/search: #4299.
- Ukrainian/Sanskrit/text transforms: #4300 and the existing Pāṇini harvest.
- Physical/science/application donors: #4301 (including radio/signal/astronomy interests).
- Knowledge/search/tooling: #4302.
- Single D10 coordination and admission boundary: #4162 / #4463.

The goal is not to make D10 bigger by historical nostalgia. It is to recover overlooked *irreducible semantic laws* from early programming, then let evidence decide whether they deserve a place.
