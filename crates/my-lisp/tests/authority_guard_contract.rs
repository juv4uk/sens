//! #115 compatibility contract after #1347.
//!
//! The old guard used to forbid host-authored semantic expectations. #1347
//! deliberately retires that policy: Rust/host code may grow local semantics.
//! The active hard boundary is asymmetric and lives in
//! `scripts/semantic-authority-guard.lisp`: host semantics must not become
//! Lisp language authority.

use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn legacy_host_authority_guard_is_non_restrictive() {
    let root = repo_root();
    let guard = fs::read_to_string(root.join("scripts/authority-guard.lisp"))
        .expect("legacy Lisp authority guard compatibility producer must exist");
    let enforcer = fs::read_to_string(root.join("scripts/authority-guard-enforce.lisp"))
        .expect("legacy Lisp authority enforcer must exist");

    assert!(guard.contains("#1347 supersedes the old deny policy"));
    assert!(guard.contains("Host/runtime/compiler/backend code and tests may contain local semantics."));
    assert!(guard.contains("(quote (authority-ok))"));

    assert!(!guard.contains("allowed-authority?"));
    assert!(!guard.contains("semantic-authority-violation"));
    assert!(!guard.contains("deletion-only"));
    assert!(!guard.contains("#112/#113"));

    // The enforcer is retained only for compatibility with existing CI wiring.
    assert!(enforcer.contains("authority-ok"));
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
