//! RED contract for #116.
//! Test definitions/expectations are Lisp-owned; backend declarations are
//! transport only. This follows the same separation used by portable Scheme
//! test definitions: definition is decoupled from execution/reporting.

use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn one_lisp_corpus_is_the_only_truth_for_native_meta_and_cml() {
    let root = repo_root();
    let adapters = fs::read_to_string(root.join("tests/fixtures/backend-adapters.lisp"))
        .expect("#116 requires a Lisp backend adapter manifest");

    assert!(adapters.contains("tests/fixtures/conformance.lisp"));
    for backend in ["native", "meta", "cml"] {
        assert!(adapters.contains(backend), "missing {backend} execution path");
    }
    assert!(!adapters.contains("expected"), "backend adapters must not own expected truth");
    assert!(!adapters.contains("error-kind"), "backend adapters must not own semantic error truth");
}
