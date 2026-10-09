# Rust Retirement Valve Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce the active #299 rule that every PR may only delete Rust: new `.rs` paths and any added Rust line are rejected before ordinary CI continues.

**Architecture:** GitHub Actions transports Rust diff facts as Lisp data. A Lisp-owned policy program returns a named verdict; a second Lisp program enforces it. The guard itself adds no Rust and does not depend on semantic classification. #304 remains separate evidence for deciding what must be preserved before deletion.

**Tech Stack:** my-lisp `.lisp`, bash/GitHub Actions, Git diff metadata.

**Spec:** `docs/superpowers/specs/2026-09-17-host-semantic-one-way-valve-design.md`

## Global Constraints

- Any added line in any `*.rs` file is forbidden.
- Any newly added `*.rs` path is forbidden even if empty.
- Rust deletion-only changes remain eligible for GREEN.
- The #300 implementation adds zero Rust lines and zero `.rs` files.
- Shell transports diff facts only; Lisp owns the allow/deny verdict.
- #115 remains an independent inner semantic-test authority guard.

---

### Task 1: RED contract and CI harness

**Files:**
- Create: `tests/fixtures/rust-retirement-valve/added-line.lisp`
- Create: `tests/fixtures/rust-retirement-valve/new-file.lisp`
- Create: `tests/fixtures/rust-retirement-valve/deletion-only.lisp`
- Create: `.github/workflows/rust-retirement-valve.yml`

**Interfaces:**
- Produces change rows shaped `(rust-change "path" additions deletions status)` where status is `new`, `existing`, or `deleted`.
- Requires `scripts/rust-retirement-valve.lisp` and `scripts/rust-retirement-valve-enforce.lisp`, intentionally absent in the RED commit.

- [ ] **Step 1:** Add synthetic forbidden and allowed change facts.
- [ ] **Step 2:** Add PR workflow that builds existing `my-lisp`, writes real Rust diff facts, and invokes the absent guard/enforcer.
- [ ] **Step 3:** Open draft PR and record CI RED caused specifically by the missing valve implementation.
- [ ] **Step 4:** Do not add any Rust while resolving RED.

### Task 2: GREEN Lisp-owned verdict

**Files:**
- Create: `scripts/rust-retirement-valve.lisp`
- Create: `scripts/rust-retirement-valve-enforce.lisp`

**Interfaces:**
- Consumes: `tests/rust-retirement-changes.lisp`.
- Produces: `(rust-retirement-ok)` or `(rust-retirement-violation PATH ADDITIONS STATUS "...")`.

- [ ] **Step 1:** Implement recursive Lisp verdict over change rows.
- [ ] **Step 2:** Reject `status = new` regardless of line count.
- [ ] **Step 3:** Reject every row with additions greater than zero.
- [ ] **Step 4:** Permit additions = 0 for existing/deleted Rust paths.
- [ ] **Step 5:** Implement fail-closed enforcer over the named verdict.
- [ ] **Step 6:** Run exact-head PR CI and require GREEN.

### Task 3: Self-test the valve directions

**Files:**
- Modify: `.github/workflows/rust-retirement-valve.yml`

**Interfaces:**
- Reuses the same Lisp guard for real PR changes and synthetic fixtures.

- [ ] **Step 1:** Verify `added-line.lisp` is rejected with path/addition diagnostics.
- [ ] **Step 2:** Verify `new-file.lisp` is rejected even with zero added lines.
- [ ] **Step 3:** Verify `deletion-only.lisp` returns `(rust-retirement-ok)`.
- [ ] **Step 4:** Restore real PR change facts before the workflow exits.

### Task 4: Integration and coordination

**Files:**
- No Rust files.

- [ ] **Step 1:** Recheck open PRs against the outer valve.
- [ ] **Step 2:** Mark Rust-growing machine/backend PRs preserved-but-frozen, not discarded.
- [ ] **Step 3:** Allow #303/#308/#310 style Lisp-growth + Rust-deletion slices to proceed after exact-head verification.
- [ ] **Step 4:** Hand #304 inventory/reachability to the local agent and keep #301/#305 preservation decisions with integration review.

## Self-review

- Spec coverage: outer invariant, deletion safety, zero-Rust implementation, diagnostics, and agent coordination are all represented.
- Placeholder scan: no TBD/TODO implementation gaps.
- Type consistency: one change-row shape and one verdict family are used throughout.
