use std::fs;
use std::path::{Path, PathBuf};

const WORKSPACE_MANIFESTS: [&str; 14] = [
    "crates/my-lisp/Cargo.toml",
    "crates/my-lisp-cli/Cargo.toml",
    "crates/my-lisp-embed/Cargo.toml",
    "crates/my-lisp-literate/Cargo.toml",
    "crates/my-lisp-wasm/Cargo.toml",
    "crates/swarm-node/Cargo.toml",
    "crates/my-lisp-host/Cargo.toml",
    "crates/my-lisp-semantic/Cargo.toml",
    "crates/my-lisp-lsp/Cargo.toml",
    "crates/wsm-guard-core/Cargo.toml",
    "crates/wsm-guard-slice/Cargo.toml",
    "crates/wsm-guard-facts/Cargo.toml",
    "crates/wsm-common-lisp-kernel/Cargo.toml",
    "crates/xtask/Cargo.toml",
];

fn workspace_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("xtask must live at <workspace>/crates/xtask")
        .to_path_buf()
}

#[test]
fn owned_workspace_crates_point_directly_to_the_single_root_license_file() {
    let root = workspace_root();
    let root_license = fs::canonicalize(root.join("LICENSE"))
        .expect("root LICENSE must exist and be canonicalizable");
    let root_manifest = fs::read_to_string(root.join("Cargo.toml"))
        .expect("workspace Cargo.toml must be readable");

    assert!(
        !root_manifest
            .lines()
            .any(|line| line.trim_start().starts_with("license-file") || line.trim_start().starts_with("license =")),
        "license metadata must stay package-local so a license-only change is not classified as a workspace dependency-graph change"
    );

    for relative in WORKSPACE_MANIFESTS {
        let manifest_path = root.join(relative);
        let manifest = fs::read_to_string(&manifest_path)
            .unwrap_or_else(|err| panic!("failed to read {relative}: {err}"));

        assert!(
            manifest.lines().any(|line| line.trim() == "license-file = \"../../LICENSE\""),
            "{relative} must point directly to the single root LICENSE"
        );
        assert!(
            !manifest.contains("license-file.workspace = true"),
            "{relative} must not inherit license metadata through [workspace.package]"
        );
        assert!(
            !manifest.lines().any(|line| line.trim_start().starts_with("license =")),
            "{relative} must not declare a second package license"
        );

        let manifest_dir = manifest_path
            .parent()
            .expect("workspace manifest path must have a parent");
        let resolved_license = fs::canonicalize(manifest_dir.join("../../LICENSE"))
            .unwrap_or_else(|err| panic!("failed to resolve {relative} license-file: {err}"));
        assert_eq!(
            resolved_license, root_license,
            "{relative} must resolve to the one root LICENSE"
        );
    }
}

fn require_authority_row(contents: &str, path: &str, test: &str, class: &str) {
    let found = contents.lines().skip(1).any(|line| {
        let fields: Vec<_> = line.split('\t').collect();
        fields.len() >= 3 && fields[0] == path && fields[1] == test && fields[2] == class
    });
    assert!(
        found,
        "#231 requires {path}::{test} to be classified as {class} before legacy semantics can be removed from canonical hard gates"
    );
}

#[test]
fn superseded_truthiness_assertions_are_explicitly_classified_before_test_transition() {
    let contents = fs::read_to_string(workspace_root().join("tests/authority-inventory.tsv"))
        .expect("tests/authority-inventory.tsv must exist");

    require_authority_row(
        &contents,
        "crates/my-lisp/tests/mccarthy.rs",
        "comparisons_chain_and_promote_exact_inexact_like_arithmetic",
        "legacy-semantic",
    );
    require_authority_row(
        &contents,
        "crates/my-lisp/tests/forward.rs",
        "match_test_condition_succeeds_when_the_expression_is_truthy",
        "legacy-semantic",
    );
    require_authority_row(
        &contents,
        "crates/my-lisp/tests/ukrainian_api_docs.rs",
        "istina_i_khyba_ie_imenamy_tyh_samykh_kanonichnykh_znachen",
        "legacy-semantic",
    );
    require_authority_row(
        &contents,
        "crates/my-lisp/tests/mccarthy.rs",
        "bare_large_integer_literals_remain_exact",
        "mixed",
    );
}

#[test]
fn semantic_fast_lane_is_lisp_owned_and_does_not_run_the_full_legacy_package_suite() {
    let root = workspace_root();
    let script = fs::read_to_string(root.join("scripts/test-current-semantic-slice.sh"))
        .expect("#231 requires scripts/test-current-semantic-slice.sh");

    assert!(
        script.contains("--test witness_authority"),
        "the fast semantic lane must execute the Lisp-owned witness observer"
    );
    assert!(
        script.contains("--test authority_guard_contract"),
        "the fast semantic lane must keep the Lisp-owned authority boundary executable"
    );
    assert!(
        script.contains("--test semantic_ref_fail_closed"),
        "the fast semantic lane must retain fail-closed semantic identity evidence"
    );
    assert!(
        !script.contains("canon_adversarial") && !script.contains("canon_language_authority"),
        "legacy host-authored Canon expectations must not define the fast canonical semantic lane"
    );

    let workflow = fs::read_to_string(root.join(".github/workflows/ci.yml"))
        .expect("CI workflow must be readable");
    assert!(
        workflow.contains("semantic=false") && workflow.contains("semantic=$semantic"),
        "PR path classification must expose an explicit semantic-change lane"
    );
    assert!(
        workflow.contains("scripts/test-current-semantic-slice.sh"),
        "PR and main fast paths must call the focused current-contract semantic script"
    );
    assert!(
        workflow.contains("steps.changes.outputs.semantic != 'true'"),
        "full package tests must be excluded from the focused semantic migration lane"
    );
}