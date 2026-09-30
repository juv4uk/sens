//! RED probe for #116.
//! One committed Lisp corpus is the exam; native, meta and CML are students.
//! This test deliberately describes the missing execution boundary only.

use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn one_lisp_truth_is_executed_by_native_meta_and_cml_without_backend_expectations() {
    let root = repo_root();
    let manifest_path = root.join("tests/fixtures/backend-adapters.lisp");
    let manifest = fs::read_to_string(&manifest_path)
        .expect("#116 requires a Lisp-owned backend adapter manifest");

    assert!(
        manifest.contains("tests/fixtures/conformance.lisp"),
        "all execution paths must name the same committed Lisp corpus"
    );
    for backend in ["native", "meta", "cml"] {
        assert!(
            manifest.contains(&format!("(backend {backend}")),
            "missing {backend} execution path"
        );
    }
    for forbidden in ["expected", "error-kind", "expected-error"] {
        assert!(
            !manifest.contains(forbidden),
            "backend transport must not own semantic truth: found `{forbidden}`"
        );
    }

    let witness = fs::read_to_string(root.join("crates/my-lisp/tests/witness_authority.rs"))
        .expect("#113 witness observer must exist");
    assert!(
        witness.contains("three_execution_paths_share_one_lisp_owned_witness"),
        "#116 is not complete until one witness is actually observed through native, meta and CML"
    );
}
