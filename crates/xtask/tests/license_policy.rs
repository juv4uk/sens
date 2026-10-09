use std::fs;
use std::path::{Path, PathBuf};

const WORKSPACE_MANIFESTS: [&str; 20] = [
    "crates/sens/Cargo.toml",
    "crates/sens-cli/Cargo.toml",
    "crates/sens-embed/Cargo.toml",
    "crates/sens-literate/Cargo.toml",
    "crates/sens-wasm/Cargo.toml",
    "crates/swarm-node/Cargo.toml",
    "crates/sens-host/Cargo.toml",
    "crates/sens-semantic/Cargo.toml",
    "crates/sens-lsp/Cargo.toml",
    "crates/wsm-guard-core/Cargo.toml",
    "crates/wsm-guard-slice/Cargo.toml",
    "crates/wsm-guard-facts/Cargo.toml",
    "crates/wsm-kernel-host/Cargo.toml",
    "crates/wsm-kernel-c-abi/Cargo.toml",
    "crates/wsm-datalog-kernel/Cargo.toml",
    "crates/wsm-prolog-kernel/Cargo.toml",
    "crates/wsm-common-lisp-kernel/Cargo.toml",
    "crates/wsm-clips-kernel/Cargo.toml",
    "crates/wsm-native-result-types/Cargo.toml",
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

fn require_authority_row_status(
    contents: &str,
    path: &str,
    test: &str,
    class: &str,
    status: &str,
) {
    let found = contents.lines().skip(1).any(|line| {
        let fields: Vec<_> = line.split('\t').collect();
        fields.len() >= 6
            && fields[0] == path
            && fields[1] == test
            && fields[2] == class
            && fields[5] == status
    });
    assert!(
        found,
        "retired test inventory must record {path}::{test} as {class}/{status}"
    );
}

#[test]
fn retired_legacy_semantics_are_absent_from_active_rust_tests() {
    let root = workspace_root();
    let contents = fs::read_to_string(root.join("tests/authority-inventory.tsv"))
        .expect("tests/authority-inventory.tsv must exist");

    for (path, test) in [
        (
            "crates/sens/tests/mccarthy.rs",
            "comparisons_chain_and_promote_exact_inexact_like_arithmetic",
        ),
        (
            "crates/sens/tests/forward.rs",
            "match_test_condition_succeeds_when_the_expression_is_truthy",
        ),
        (
            "crates/sens/tests/ukrainian_api_docs.rs",
            "istina_i_khyba_ie_imenamy_tyh_samykh_kanonichnykh_znachen",
        ),
    ] {
        require_authority_row_status(&contents, path, test, "legacy-semantic", "retired");
        let source = fs::read_to_string(root.join(path))
            .unwrap_or_else(|err| panic!("failed to read {path}: {err}"));
        assert!(
            !source.contains(&format!("fn {test}(")),
            "retired legacy-semantic assertion still exists: {path}::{test}"
        );
    }

    let forward = fs::read_to_string(root.join("crates/sens/tests/forward.rs"))
        .expect("forward.rs must exist");
    assert!(
        !forward.contains("fn match_test_condition_fails_when_the_expression_is_falsy("),
        "the paired generic-truthiness failure assertion must also be retired"
    );

    let uk = fs::read_to_string(root.join("crates/sens/tests/ukrainian_api_docs.rs"))
        .expect("ukrainian_api_docs.rs must exist");
    assert!(
        uk.contains("fn novi_predykatni_nazvy_i_stari_aliasy_vykonuiutsia_odnakovo("),
        "keep the surface-alias equivalence check"
    );

    let mccarthy = fs::read_to_string(root.join("crates/sens/tests/mccarthy.rs"))
        .expect("mccarthy.rs must exist");
    assert!(
        mccarthy.contains("fn numeric_comparisons_return_exact_predicate_bits("),
        "retain current exact PredicateBit comparison coverage"
    );
    assert!(
        !mccarthy.contains("(not? (quote ()))"),
        "Rust tests must not pin the retired not?/truthy? implementation to the t/() sentinel"
    );
    assert!(
        !mccarthy.contains("fn comparisons_chain_and_promote_exact_inexact_like_arithmetic("),
        "superseded comparison-to-t/() assertion must not return"
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