//! Contract for #115: the semantic allow/deny rule itself is Lisp-owned.
//! Rust verifies the boundary shape; CI only transports change facts, shows
//! the Lisp-owned verdict, and invokes the Lisp-owned enforcer.

use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn authority_policy_is_lisp_owned_and_explicit() {
    let root = repo_root();
    let guard = fs::read_to_string(root.join("scripts/authority-guard.lisp"))
        .expect("#115 Lisp authority guard must exist");
    let inventory = fs::read_to_string(root.join("tests/authority-inventory.lisp"))
        .expect("#115 Lisp-readable authority inventory must exist");

    assert!(guard.contains("allowed-authority?") && guard.contains("observer") && guard.contains("mechanism"));
    assert!(guard.contains("semantic-authority-violation") && guard.contains("#112/#113"));
    assert!(
        guard.contains("(structural-kind empty-list)")
            && guard.contains("(structural-kind pair)")
            && guard.contains("(identity-relation same)")
            && guard.contains("(identity-relation distinct)"),
        "authority policy must consume explicit structural/identity results"
    );
    assert!(
        !guard.contains("(t ") && !guard.contains("(car ())"),
        "verdict producer must not depend on historical truthiness or intentional failure"
    );
    assert!(inventory.contains("forbidden-semantic.rs\" semantic-authority"));
    assert!(inventory.contains("allowed-mechanism.rs\" mechanism"));
    assert!(!root.join("scripts/semantic_authority_guard.py").exists(),
        "Python must not own the semantic authority verdict");
}

#[test]
fn authority_migration_allows_only_deletion_only_host_test_changes() {
    let root = repo_root();
    let guard = fs::read_to_string(root.join("scripts/authority-guard.lisp"))
        .expect("#115 Lisp authority guard must exist");
    let ci = fs::read_to_string(root.join(".github/workflows/ci.yml"))
        .expect("CI workflow must exist");

    assert!(
        guard.contains("deletion-only"),
        "Lisp guard must explicitly own the one-way authority-reduction rule"
    );
    assert!(
        ci.contains("git diff --numstat") && ci.contains("deletion-only") && ci.contains("(change"),
        "host CI may transport diff direction as data, but may not decide authority"
    );
}

#[test]
fn authority_diagnostic_and_failure_are_separate_lisp_processes() {
    let root = repo_root();
    let guard = fs::read_to_string(root.join("scripts/authority-guard.lisp"))
        .expect("#115 Lisp authority guard must exist");
    let enforcer = fs::read_to_string(root.join("scripts/authority-guard-enforce.lisp"))
        .expect("#115 Lisp authority enforcer must exist");
    let ci = fs::read_to_string(root.join(".github/workflows/ci.yml"))
        .expect("CI workflow must exist");

    assert!(!guard.contains("(car ())"),
        "verdict producer must complete successfully so its diagnostic cannot be rolled back");
    assert!(
        enforcer.contains("semantic-authority-violation") && enforcer.contains("(car ())"),
        "a second Lisp process must own fail-closed enforcement"
    );
    assert!(
        ci.contains("> tests/authority-verdict.lisp")
            && ci.contains("cat tests/authority-verdict.lisp")
            && ci.contains("scripts/authority-guard-enforce.lisp"),
        "CI may transport/show the Lisp verdict and invoke Lisp enforcement, but may not interpret authority itself"
    );
}
