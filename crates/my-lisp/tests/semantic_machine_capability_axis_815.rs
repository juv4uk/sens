//! #815 observer: target-neutral machine capability projection.
//! This test checks provenance/authority boundaries only.

use std::fs;
use std::path::PathBuf;

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(relative)
}

fn read(relative: &str) -> String {
    fs::read_to_string(repo_file(relative)).unwrap_or_else(|e| panic!("{relative}: {e}"))
}

#[test]
fn target_neutral_capability_axis_is_registry_backed_and_non_authoritative() {
    let axis = read("contracts/semantic-machine-capability-axis-815.lisp");
    let registry = read("lib/surface/semantic-registry.lisp");
    let provenance = read("lib/machine/capability-provenance.lisp");

    for sid in ["00001100", "00000011", "00000111", "00000100", "00000101", "00000110"] {
        assert!(registry.contains(&format!("(\"{sid}\" ")), "SID {sid} must come from sr/2");
        assert!(axis.contains(&format!("(sid . \"{sid}\")")), "axis missing {sid}");
    }

    for capability in [
        "bounded-integer-add",
        "equality-compare",
        "conditional-branch",
        "pair-field-store",
        "pair-field-load-head",
        "pair-field-load-tail",
    ] {
        assert!(!registry.contains(capability), "capability {capability} leaked into semantic registry");
    }

    for provenance_name in ["add-u64", "eq-cond-u64", "car-cons-u64"] {
        assert!(provenance.contains(&format!("(name {provenance_name})")), "missing provenance {provenance_name}");
    }

    assert!(axis.contains("(status . no-execution-witness)"));
    assert!(axis.contains("(provenance . ())"));
    assert!(!axis.contains("(semantic-id ."));
}