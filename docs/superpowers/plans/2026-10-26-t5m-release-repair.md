# T5M Release Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Restore a compilable T5M-only SENS release path and restart the `s0.42.1` release from a corrected SHA.

**Architecture:** Keep T5M transport in the Zig corridor. Remove Rust references to the retired ternary transport placeholder and correct the malformed branch left after removing the unadmitted CODE-CHAR bridge. The existing release smoke test is the regression witness.

**Tech Stack:** Rust, Zig/T5M, GitHub Actions.

**Spec:** `AGENTS.md` owner decisions of 25–26.10.2026; user instruction of 26.10.2026.

## Global Constraints

- Active physical transport is Zig/T5M; do not restore Rust T5 or ternary fallback.
- Keep release RED visible until the exact tagged SHA passes the release workflow.
- Do not change SENS semantic laws in this technical repair.

## Review Focus

- `cargo test --locked -p sens-cli --test binary_t5m_zig_roundtrip` must compile and execute without Rust ternary exports.
- Removing CODE-CHAR compatibility must leave `mixed_source` syntactically valid.
- Retag only a committed corrected SHA; never retag an unchanged failing SHA.

---

### Task 1: Remove stale Rust transport surface and repair the parser branch

**Files:**
- Modify: `crates/sens/src/lib.rs`
- Modify: `crates/sens/src/mixed_source.rs`
- Test: `crates/sens-cli/tests/binary_t5m_zig_roundtrip.rs`

**Interfaces:**
- Consumes: Zig/T5M physical corridor used by the release smoke test.
- Produces: a Rust crate that no longer compiles the retired `ternary_transport` placeholder under test configuration.

- [ ] **Step 1: Reproduce the existing release smoke failure**

Run: `cargo test --locked -p sens-cli --test binary_t5m_zig_roundtrip`
Expected: FAIL while compiling `sens` because the malformed CODE-CHAR removal and stale ternary re-exports are present.

- [ ] **Step 2: Remove the retired test-only `ternary_transport` module declaration and public re-exports from `crates/sens/src/lib.rs`**

The T5M Zig corridor remains the physical implementation.

- [ ] **Step 3: Restore the `else if matches!` branch delimiter in `crates/sens/src/mixed_source.rs` without restoring the CODE-CHAR bridge**

- [ ] **Step 4: Verify the release smoke test passes**

Run: `cargo test --locked -p sens-cli --test binary_t5m_zig_roundtrip`
Expected: PASS.

### Task 2: Commit and restart the release from the corrected SHA

**Files:**
- Modify: Git ref `s0.42.1`

**Interfaces:**
- Consumes: a committed Task 1 repair and successful local release smoke test.
- Produces: `s0.42.1` pointed at the repaired commit and a newly triggered release workflow.

- [ ] **Step 1: Commit the Task 1 repair**

- [ ] **Step 2: Move `s0.42.1` only to that commit and push it**

- [ ] **Step 3: Record the exact GitHub Actions URL and its final result**

