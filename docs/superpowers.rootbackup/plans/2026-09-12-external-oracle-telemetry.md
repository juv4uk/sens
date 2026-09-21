# External Oracle та доказова телеметрія — план реалізації

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Побудувати детермінований `external-oracle/1` bridge, який формально перекладає exact-arithmetic AST my-lisp у Wolfram Language, валідовує відповідь проти corpus authority та породжує evidence і PostHog JSONL без прихованих мережевих викликів.

**Architecture:** `xtask` читає чинні `conformance.my` та `inventory.my`, резолвить голови arithmetic forms через semantic registry і генерує версійований request. Окремий verify-крок імпортує зовнішній response, запускає доступні backend-и, чесно класифікує відсутнє покриття та створює WSM evidence і JSONL-проєкцію; звичайний CI лишається offline.

**Tech Stack:** Rust workspace, `my-lisp` parser/evaluator API, `serde`/`serde_json` лише для PostHog-проєкції, GitHub Actions, machine-readable `.my` evidence.

**Spec:** `docs/superpowers/specs/2026-09-12-external-oracle-telemetry-design.md`

## Global Constraints

- Українська є первинною мовою нового prose та коментарів; identifiers і protocol literals лишаються англійськими.
- `language-contract.my` і наявні expected/error поля `conformance.my` не змінюються.
- Registry визначає spelling → semantic ID; adapter hardcode-ить лише власну скінченну проєкцію semantic ID → Wolfram operation.
- `unsupported` ніколи не рахується як `pass`; historical evidence не рахується current.
- Жодних Wolfram/PostHog ключів у коді, evidence, test fixtures або логах.
- Production-код кожної задачі пишеться лише після test-only commit і підтвердженого RED у GitHub Actions або штатному WSL2 + Guix середовищі.
- Звичайний PR CI не залежить від зовнішньої мережі.

---

### Task 1: Registry reverse projection

**Files:**
- Modify: `crates/my-lisp/src/lib.rs`
- Test: `crates/my-lisp/src/semantic_registry.rs`

**Interfaces:**
- Consumes: `semantic_registry::admitted_semantic_id_for_surface(&str)`.
- Produces: `my_lisp::semantic_registry_export::semantic_id_for_admitted_surface(name: &str) -> Option<&'static str>`.

- [ ] **Step 1: Write the failing public-boundary test**

Append inside the existing `semantic_registry` test module:

```rust
#[test]
fn public_reverse_projection_preserves_identity_across_admitted_surfaces() {
    for surface in admitted_surfaces_for_semantic_id("1003") {
        assert_eq!(
            crate::semantic_registry_export::semantic_id_for_admitted_surface(surface),
            Some("1003")
        );
    }
    assert_eq!(
        crate::semantic_registry_export::semantic_id_for_admitted_surface("not-a-surface"),
        None
    );
}
```

Break caught: an external adapter starts comparing literal spellings or cannot resolve non-symbolic admitted surfaces to the division identity.

- [ ] **Step 2: Commit and push the RED state**

```bash
git add crates/my-lisp/src/semantic_registry.rs
git commit -m "test: require public semantic identity lookup"
git push -u origin feat/wsm-5-external-oracle
```

Run through GitHub Actions: `cargo test -p my-lisp public_reverse_projection_preserves_identity_across_admitted_surfaces`.

Expected: compile failure because `semantic_id_for_admitted_surface` does not exist.

- [ ] **Step 3: Add the minimal public projection**

Inside `semantic_registry_export` in `crates/my-lisp/src/lib.rs` add:

```rust
/// Повертає opaque semantic ID для stable або compatibility-only surface.
/// Значення операції лишається у мовному контракті, не в цій проєкції.
pub fn semantic_id_for_admitted_surface(name: &str) -> Option<&'static str> {
    super::semantic_registry::admitted_semantic_id_for_surface(name)
}
```

- [ ] **Step 4: Verify GREEN and commit**

```bash
cargo test -p my-lisp public_reverse_projection_preserves_identity_across_admitted_surfaces
cargo test -p my-lisp semantic_registry
git add crates/my-lisp/src/lib.rs crates/my-lisp/src/semantic_registry.rs
git commit -m "feat: expose admitted surface identity lookup"
```

Expected: both test commands pass with zero failures.

---

### Task 2: Exact AST → Wolfram Language translator

**Files:**
- Modify: `crates/xtask/Cargo.toml`
- Create: `crates/xtask/src/external_oracle.rs`
- Modify: `crates/xtask/src/main.rs`

**Interfaces:**
- Consumes: `my_lisp::{parse, Exactness, Expr, ExprKind}` and `semantic_id_for_admitted_surface` from Task 1.
- Produces: `pub(crate) fn translate_source(source: &str) -> Result<String, Unsupported>` and `Unsupported { code: &'static str, detail: String }`.

- [ ] **Step 1: Add module-local failing tests before implementation**

Create `crates/xtask/src/external_oracle.rs` containing only the error type, wished-for function declaration as an `unimplemented!()`, and tests with hand-derived literals:

```rust
#[derive(Debug, Eq, PartialEq)]
pub(crate) struct Unsupported {
    pub(crate) code: &'static str,
    pub(crate) detail: String,
}

pub(crate) fn translate_source(_source: &str) -> Result<String, Unsupported> {
    unimplemented!("exact AST to Wolfram translation")
}

#[cfg(test)]
mod tests {
    use super::translate_source;

    #[test]
    fn nary_division_is_a_left_fold_not_ratio_divided_by_ratio() {
        assert_eq!(
            translate_source("(/ 5 6 8 7)").unwrap(),
            "Fold[Divide, {5, 6, 8, 7}]"
        );
    }

    #[test]
    fn explicit_nested_division_preserves_the_different_tree() {
        assert_eq!(
            translate_source("(/ (/ 5 6) (/ 8 7))").unwrap(),
            "Divide[Fold[Divide, {5, 6}], Fold[Divide, {8, 7}]]"
        );
    }

    #[test]
    fn unary_and_identity_arities_are_preserved() {
        assert_eq!(translate_source("(- 1/3)").unwrap(), "Minus[1/3]");
        assert_eq!(translate_source("(/ 4)").unwrap(), "Divide[1, 4]");
        assert_eq!(translate_source("(+)").unwrap(), "0");
        assert_eq!(translate_source("(*)").unwrap(), "1");
    }
}
```

Expose `mod external_oracle;` from `main.rs` and add `my-lisp = { path = "../my-lisp" }` to `xtask` dependencies so the test compiles up to the deliberate panic.

Break caught: regrouping n-ary `/`, losing unary semantics, or inventing zero-argument arithmetic behavior.

- [ ] **Step 2: Verify RED**

```bash
cargo test -p xtask external_oracle::tests -- --nocapture
```

Expected: tests execute and fail at `unimplemented!("exact AST to Wolfram translation")`.

- [ ] **Step 3: Implement the minimal recursive translator**

Implement these exact boundaries:

```rust
const ADD_ID: &str = "0104";
const SUBTRACT_ID: &str = "1001";
const MULTIPLY_ID: &str = "1002";
const DIVIDE_ID: &str = "1003";

pub(crate) fn translate_source(source: &str) -> Result<String, Unsupported> {
    let forms = my_lisp::parse(source).map_err(|error| Unsupported {
        code: "parse-error",
        detail: error.to_string(),
    })?;
    let [form] = forms.as_slice() else {
        return Err(Unsupported {
            code: "top-level-form-count",
            detail: format!("expected exactly one form, observed {}", forms.len()),
        });
    };
    translate_expr(form)
}
```

`translate_expr` admits only `Number(_, Exact)`, `Rational` and proper `List`. It resolves the head symbol with `semantic_id_for_admitted_surface`; `Number(_, Inexact)`, strings, buffers, pairs, bare symbols and unknown IDs return stable `Unsupported.code` values. Arithmetic shapes are:

```rust
fn render_operation(id: &str, args: &[String]) -> Result<String, Unsupported> {
    match (id, args) {
        (ADD_ID, []) => Ok("0".into()),
        (ADD_ID, _) => Ok(format!("Plus[{}]", args.join(", "))),
        (MULTIPLY_ID, []) => Ok("1".into()),
        (MULTIPLY_ID, _) => Ok(format!("Times[{}]", args.join(", "))),
        (SUBTRACT_ID, [one]) => Ok(format!("Minus[{one}]")),
        (SUBTRACT_ID, []) => Err(arity("subtract", "at-least-one")),
        (SUBTRACT_ID, _) => Ok(format!("Fold[Subtract, {{{}}}]", args.join(", "))),
        (DIVIDE_ID, [one]) => Ok(format!("Divide[1, {one}]")),
        (DIVIDE_ID, []) => Err(arity("divide", "at-least-one")),
        (DIVIDE_ID, [left, right]) => Ok(format!("Divide[{left}, {right}]")),
        (DIVIDE_ID, _) => Ok(format!("Fold[Divide, {{{}}}]", args.join(", "))),
        _ => Err(Unsupported {
            code: "unsupported-semantic-id",
            detail: id.to_string(),
        }),
    }
}
```

- [ ] **Step 4: Add unsupported and surface-identity tests**

```rust
#[test]
fn admitted_surface_peers_translate_by_identity() {
    assert_eq!(translate_source("(поділити 5 6 8 7)"), translate_source("(/ 5 6 8 7)"));
}

#[test]
fn effects_and_approximate_values_are_never_guessed() {
    assert_eq!(translate_source("(print 1)").unwrap_err().code, "unsupported-semantic-id");
    assert_eq!(translate_source("1 2").unwrap_err().code, "top-level-form-count");
}
```

`поділити` взято безпосередньо з чинного stable UK surface рядка `1003` у `lib/surface/semantic-registry.wsm`.

- [ ] **Step 5: Verify GREEN, mutation protection, and commit**

```bash
cargo test -p xtask external_oracle::tests -- --nocapture
```

Temporarily replace the n-ary division arm with `Divide[args[0], Divide[args[1], …]]`; rerun and confirm `nary_division_is_a_left_fold_not_ratio_divided_by_ratio` fails. Restore the implementation and rerun GREEN.

```bash
git add crates/xtask/Cargo.toml crates/xtask/src/main.rs crates/xtask/src/external_oracle.rs Cargo.lock
git commit -m "feat(xtask): translate exact Lisp AST to Wolfram"
```

---

### Task 3: Corpus-driven request export

**Files:**
- Modify: `crates/xtask/src/external_oracle.rs`
- Modify: `crates/xtask/src/main.rs`
- Create: `crates/xtask/tests/external_oracle_cli.rs`

**Interfaces:**
- Consumes: `translate_source`, `tests/fixtures/conformance.my`, `tests/fixtures/inventory.my`, `language-contract.my`.
- Produces: `ExternalOracleRequest`, `load_fixture(repo_root, fixture_id)`, `render_request(&ExternalOracleRequest)`, and CLI `external-oracle export --fixture <F-ID>`.

- [ ] **Step 1: Write black-box CLI RED test**

```rust
use std::process::Command;

#[test]
fn exports_the_live_exact_division_fixture_as_versioned_request() {
    let repo = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo)
        .args(["external-oracle", "export", "--fixture", "F-8bc31cae9e7e39b9"])
        .output()
        .unwrap();
    assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert!(stdout.contains("(protocol . external-oracle/1)"));
    assert!(stdout.contains("(contract-revision . (6 0))"));
    assert!(stdout.contains("(query . \"Fold[Divide, {5, 6, 8, 7}]\")"));
    assert!(stdout.contains("(expected . \"5/336\")"));
}
```

Break caught: CLI reads a hand-copied fixture, loses contract provenance, or exports the wrong arithmetic tree.

- [ ] **Step 2: Verify RED**

```bash
cargo test -p xtask --test external_oracle_cli exports_the_live_exact_division_fixture_as_versioned_request -- --nocapture
```

Expected: failure because `external-oracle` is not a recognized subcommand.

- [ ] **Step 3: Implement fail-closed corpus/inventory pairing**

Add:

```rust
pub(crate) struct ExternalOracleRequest {
    pub(crate) fixture_id: String,
    pub(crate) source_digest: String,
    pub(crate) contract_major: u64,
    pub(crate) contract_minor: u64,
    pub(crate) query: String,
    pub(crate) expected: String,
}
```

Parse both data files with `my_lisp::parse`. Reject unequal fixture counts, duplicate IDs, absent `expected`, missing `S1`, and any selected source that `translate_source` rejects. Derive the digest with `my_lisp::sha256_source(source.as_bytes())`; render lowercase hex with a local mechanical helper. Parse `(major . 6)` and `(minor . 0)` from `language-contract.my` instead of hardcoding `6 0`.

- [ ] **Step 4: Wire the CLI without side effects**

`main.rs` dispatch becomes:

```rust
Some("external-oracle") => match external_oracle::run(args.collect()) {
    Ok(output) => {
        println!("{output}");
        ExitCode::SUCCESS
    }
    Err(error) => {
        eprintln!("external-oracle failed: {error}");
        ExitCode::FAILURE
    }
},
```

The export path writes only stdout. It does not call Wolfram, PostHog or the filesystem beyond reading repository authority files.

- [ ] **Step 5: Add drift and unknown-ID tests, verify, commit**

Unit tests pass controlled in-memory corpus/inventory strings to the loader and assert exact errors for count mismatch, duplicate ID and missing fixture. Then run:

```bash
cargo test -p xtask --test external_oracle_cli -- --nocapture
cargo test -p xtask external_oracle::tests -- --nocapture
git add crates/xtask/src/main.rs crates/xtask/src/external_oracle.rs crates/xtask/tests/external_oracle_cli.rs
git commit -m "feat(xtask): export corpus-bound oracle requests"
```

---

### Task 4: Response validation, backend observations, evidence and PostHog projection

**Files:**
- Modify: `crates/xtask/Cargo.toml`
- Modify: `crates/xtask/src/external_oracle.rs`
- Modify: `crates/xtask/src/main.rs`
- Modify: `crates/xtask/tests/external_oracle_cli.rs`
- Create: `tests/fixtures/external-oracle/wolfram-F-8bc31cae9e7e39b9.my`

**Interfaces:**
- Consumes: an `external-oracle/1` request and response, native/meta evaluator APIs, corpus backend tags.
- Produces: `VerifiedObservation`, WSM evidence rendering, JSONL event rendering, CLI `external-oracle verify --fixture <F-ID> --response <path>`.

- [ ] **Step 1: Add the real Wolfram response fixture**

Record the already-observed exact result, without credentials:

```lisp
(external-oracle-response
  (protocol . external-oracle/1)
  (fixture-id . "F-8bc31cae9e7e39b9")
  (source-digest . "sha256:7aad8d5b880cdf544a07fd5590e98262d88d99c342d2a9cfbace07670f97d37c")
  (contract-revision . (6 0))
  (oracle . wolfram-language)
  (actual . "5/336")
  (duration-ms . 0)
  (run-id . "wolfram-plugin-2026-09-12"))
```

The concrete digest is the SHA-256 of the exact UTF-8 source bytes `(/ 5 6 8 7)` and matches the existing `oracle-results.my` provenance; `duration-ms` remains zero because the connector did not return a measured kernel duration.

- [ ] **Step 2: Write validation RED tests**

```rust
#[test]
fn verified_response_produces_pass_evidence_and_one_json_event() {
    let result = verify_fixture(&request(), &response("5/336")).unwrap();
    assert_eq!(result.external.outcome, Outcome::Pass);
    assert!(result.evidence.contains("(result . pass)"));
    let event: serde_json::Value = serde_json::from_str(&result.posthog_jsonl).unwrap();
    assert_eq!(event["event"], "lisp_oracle_case_completed");
    assert_eq!(event["properties"]["fixture_id"], "F-8bc31cae9e7e39b9");
    assert_eq!(event["properties"]["actual"], "5/336");
}

#[test]
fn protocol_mismatch_cannot_emit_telemetry() {
    let error = verify_fixture(&request(), &response_with_wrong_digest()).unwrap_err();
    assert_eq!(error.code, "source-digest-mismatch");
}

#[test]
fn exact_disagreement_is_preserved_as_mismatch_evidence() {
    let result = verify_fixture(&request(), &response("35/48")).unwrap();
    assert_eq!(result.external.outcome, Outcome::Mismatch);
    assert!(result.evidence.contains("(result . fail)"));
}
```

Break caught: emitting analytics before validation, collapsing mismatch into protocol error, or using approximate/string-only equality.

- [ ] **Step 3: Verify RED**

```bash
cargo test -p xtask verified_response -- --nocapture
cargo test -p xtask protocol_mismatch -- --nocapture
cargo test -p xtask exact_disagreement -- --nocapture
```

Expected: compile failures because verifier types and functions do not exist.

- [ ] **Step 4: Implement validated observations**

Define:

```rust
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "kebab-case")]
pub(crate) enum Outcome { Pass, Mismatch, Unsupported, Error }

pub(crate) struct BackendObservation {
    pub(crate) backend: &'static str,
    pub(crate) oracle: &'static str,
    pub(crate) observation_source: &'static str,
    pub(crate) evidence_class: &'static str,
    pub(crate) actual: Option<String>,
    pub(crate) outcome: Outcome,
    pub(crate) reason: Option<String>,
}
```

Validation order is protocol → fixture ID → digest → contract revision → oracle name → parse exactly one `actual` numeric form → reject `Inexact` → compare normalized `Value::to_string()` with corpus expected. Only after this function returns `Ok(VerifiedRun)` may renderers run.

Native observation evaluates the source with `load_core_library` and compares to corpus expected. Meta observation runs the existing `my-eval` path; a match is `pass`, otherwise `(meta-eval-gap . t)` permits only `unsupported`. WSM-native without imported executable evidence becomes `unsupported/no-executable-evidence`; do not infer success from prose.

Add `serde = { version = "1", features = ["derive"] }` and `serde_json = "1"` to `xtask`. JSON is a projection only; WSM evidence remains the durable record.

- [ ] **Step 5: Add CLI output modes and integration test**

`verify` accepts `--format evidence|posthog-jsonl|report`. The black-box test invokes all three and asserts:

- evidence contains fixture ID, query, expected, actual, commit, contract revision and `result . pass`;
- JSON parses and contains all required properties;
- report names `native`, `meta-eval`, `wsm-native`, and `wolfram-language` separately.

- [ ] **Step 6: Verify GREEN and commit**

```bash
cargo test -p xtask -- --nocapture
cargo run -p xtask -- external-oracle export --fixture F-8bc31cae9e7e39b9
cargo run -p xtask -- external-oracle verify --fixture F-8bc31cae9e7e39b9 --response tests/fixtures/external-oracle/wolfram-F-8bc31cae9e7e39b9.my --format report
git add Cargo.lock crates/xtask tests/fixtures/external-oracle
git commit -m "feat(xtask): verify oracle evidence and telemetry"
```

---

### Task 5: Durable witness, CI gate and documentation

**Files:**
- Create: `evidence/S1/wolfram/4f1b454.my`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/testing.md`
- Modify: `docs/superpowers/plans/2026-09-12-external-oracle-telemetry.md`

**Interfaces:**
- Consumes: verified CLI from Task 4.
- Produces: committed external witness and offline CI regression gate.

- [ ] **Step 1: Generate, do not hand-copy, the evidence file**

```bash
mkdir -p evidence/S1/wolfram
cargo run -p xtask -- external-oracle verify \
  --fixture F-8bc31cae9e7e39b9 \
  --response tests/fixtures/external-oracle/wolfram-F-8bc31cae9e7e39b9.my \
  --format evidence > evidence/S1/wolfram/4f1b454.my
./target/debug/my-lisp --oracle-check evidence/S1/wolfram/4f1b454.my
```

Expected: `(outcome valid)` and one top-level evidence form.

- [ ] **Step 2: Add the offline CI gate**

Add after the workspace tests in `.github/workflows/ci.yml`:

```yaml
      - name: Verify external exact-arithmetic oracle witness
        run: |
          cargo run -p xtask -- external-oracle export --fixture F-8bc31cae9e7e39b9
          cargo run -p xtask -- external-oracle verify \
            --fixture F-8bc31cae9e7e39b9 \
            --response tests/fixtures/external-oracle/wolfram-F-8bc31cae9e7e39b9.my \
            --format report
```

Break caught: registry/AST/corpus/protocol drift invalidates the checked-in live response.

- [ ] **Step 3: Document the executable boundary**

Add one Ukrainian-primary row to `docs/testing.md` naming:

```text
xtask external-oracle — formal AST→Wolfram request, digest/revision response validation,
native/meta/WSM status separation, WSM evidence and PostHog JSONL projection; live network
execution remains a manual/scheduled host concern and does not block ordinary PR CI.
```

- [ ] **Step 4: Run full verification**

```bash
cargo fmt --all -- --check
cargo test --workspace
cargo build --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo run -p xtask -- verify
python3 scripts/uk-latynka.py self-test
git diff --check
```

Expected: every command exits zero; test and clippy output contains no failures or warnings.

- [ ] **Step 5: Update the plan checkboxes and commit**

Mark only actually executed steps `[x]`, then:

```bash
git add .github/workflows/ci.yml docs/testing.md docs/superpowers/plans/2026-09-12-external-oracle-telemetry.md evidence/S1/wolfram/4f1b454.my
git commit -m "ci: gate external exact arithmetic evidence"
```

- [ ] **Step 6: Push and verify GitHub Actions**

```bash
git push origin feat/wsm-5-external-oracle
```

Confirm the branch's `CI` workflow shows green for `cargo test --workspace`, build, clippy, xtask verification and the external oracle witness step. If any job fails, preserve the logs and return to the relevant RED/GREEN task rather than marking this plan complete.
