//! #1347 active asymmetric authority boundary.
//!
//! Rust/host code may carry local mechanism semantics. The hard boundary is
//! one-way: host semantics must not become Lisp language authority.

use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn active_boundary_is_the_asymmetric_host_to_lisp_firewall() {
    let root = repo_root();
    let guard = fs::read_to_string(root.join("scripts/semantic-authority-guard.lisp"))
        .expect("#1347 asymmetric semantic firewall must exist");
    let ci = fs::read_to_string(root.join(".github/workflows/ci.yml"))
        .expect("CI workflow must exist");

    assert!(guard.contains("host-to-language-authority-leak"));
    assert!(guard.contains("language-authority-source?"));
    assert!(guard.contains("allowed-local-implementation"));

    assert!(
        ci.contains("*.lisp|*.wsm|*.my"),
        "CI must feed Lisp-owned sources to the asymmetric firewall"
    );
    assert!(
        !ci.contains("new host-side semantic authority requires explicit review"),
        "CI must not retain the retired #1049 host-semantics policy"
    );
}
