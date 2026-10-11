//! RED contract for #116. Backends may provide mechanism-only adapters, while
//! the committed Lisp corpus remains the single source of expected truth.

use std::fs;
use std::path::PathBuf;

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(relative)
}

#[test]
fn backend_adapter_manifest_points_all_paths_at_one_lisp_corpus_without_expected_literals() {
    let manifest = fs::read_to_string(repo_file("tests/fixtures/backend-adapters.lisp"))
        .expect("#116 requires a data-only Lisp backend adapter manifest");

    for backend in ["native", "meta", "cml"] {
        assert!(
            manifest.contains(&format!("(backend {backend}")),
            "adapter manifest must declare {backend}"
        );
    }
    assert!(
        manifest.contains("tests/fixtures/conformance.lisp"),
        "all adapters must point to the one committed Lisp witness corpus"
    );
    assert!(
        !manifest.contains("(expected ") && !manifest.contains("(error-kind "),
        "adapter metadata must not grow a second semantic truth table"
    );
}
