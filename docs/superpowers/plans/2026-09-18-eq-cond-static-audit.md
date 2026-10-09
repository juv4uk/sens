# EQ vs COND Static-Datum Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether canonical three-part `cond` can replace `PRIM_EQ` for its current two-runtime-operand atomic identity semantics.

**Architecture:** Keep all persistent changes under `docs/research/471/**` plus this plan. Execute only live evaluator probes in a verification-only child branch using a temporary integration test removed before diff hygiene. No production semantic changes.

**Tech Stack:** my-lisp evaluator, canonical three-part `cond`, `eq`, GitHub Actions, temporary Rust integration observer.

**Spec:** GitHub issue #471.

## Global Constraints

- No production evaluator, Canon registry, semantic fixture, machine, or Rust semantic producer changes.
- Current EQ result algebra remains `(identity-relation same|distinct)`; pair operands remain outside EQ domain with named `Type`.
- Canonical three-part COND evaluates its query but quotes its expected form; do not assume the expected form is a runtime operand.
- Do not use migration-only two-part COND as authority.
- No macro/registry alias or host equality oracle may stand in for a derivation.
- Result classification must remain bounded to the executed route.

---

### Task 1: Record the falsifiable capability comparison

**Files:**
- Create: `docs/research/471/eq-cond-static-boundary.lisp`

**Interfaces:**
- Consumes: `contracts/structural-observation-contract.lisp`, `contracts/control-dispatch-contract.lisp`, live evaluator semantics.
- Produces: pre-execution predictions.

- [ ] **Step 1:** Record current capability shapes:

```text
EQ(left-runtime, right-runtime) -> same|distinct, atom-domain only
COND(query-runtime, expected-source-datum, branch) -> selection by actual == quoted(expected-form)
```

- [ ] **Step 2:** Record predictions:
  - literal atom match through COND succeeds;
  - literal pair match through COND succeeds although EQ(pair,pair) is Type;
  - dynamic same values passed through variables produce a false-negative if the variable name is used as COND's expected form;
  - dynamic distinct values can produce a false-positive when the left runtime value equals the expected variable's *name*.

- [ ] **Step 3:** Pre-classify as `insufficient-evidence`; explicitly forbid a conclusion before execution.

### Task 2: Execute live probes in a NEVER-MERGE child

**Files:**
- Child only: `.github/workflows/verify-471-eq-cond-static.yml`
- Runner temporary only: `crates/my-lisp/tests/verify_471_eq_cond_static.rs`

- [ ] **Step 1:** Verify current EQ dynamic behavior:
  - same runtime symbols -> `identity-relation same`;
  - distinct runtime symbols -> `identity-relation distinct`;
  - pair operands -> `Type`.

- [ ] **Step 2:** Verify canonical COND static-datum behavior:
  - static atom actual vs atom datum -> selected;
  - static pair actual vs pair datum -> selected.

- [ ] **Step 3:** Verify dynamic-variable mismatch:
  - `left=radio,right=radio` with clause `(left right ...)` does not match because expected datum is symbol `right`;
  - `left=right,right=radio` with the same clause does match, proving syntax-name capture rather than runtime-RHS comparison.

- [ ] **Step 4:** Remove temporary test and run `git diff --check`; close child PR without merge.

### Task 3: Classify the route and verify the research PR

**Files:**
- Modify: `docs/research/471/eq-cond-static-boundary.lisp`

- [ ] **Step 1:** Record exact PR/run/head/test counts.
- [ ] **Step 2:** If predictions hold, classify:
  - `COND-static-datum -> EQ-dynamic-atom` = `route-falsified`;
  - relationship = `capability-incomparable-under-tested-observations`.
- [ ] **Step 3:** Explain why: COND compares broader static data including pairs, while EQ compares two runtime operands but only atoms.
- [ ] **Step 4:** Run exact-head CI + bilingual gate for the research PR.
- [ ] **Step 5:** Feed only the bounded result to #471 and #419; do not edit the Canon demolition map automatically.
