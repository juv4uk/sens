use std::fs;
use std::path::PathBuf;

fn repo_file(path: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(path)
}

#[test]
fn machine_layer_has_explicit_noninterference_contract() {
    let path = repo_file("lib/machine/authority-boundary.lisp");
    let contract = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("#150 requires {}: {error}", path.display()));

    for fact in [
        "(semantic-authority my-lisp)",
        "(semantic-id-from-isa forbidden)",
        "(lowering-direction semantic-to-machine)",
        "(reverse-authority machine-to-semantic forbidden)",
        "(machine-public-api-admission explicit-ratification-only)",
    ] {
        assert!(contract.contains(fact), "#150 boundary missing `{fact}`");
    }
}

#[test]
fn synthetic_machine_mnemonic_is_not_a_public_semantic_identity() {
    let registry = fs::read_to_string(repo_file("lib/semantic-registry.lisp"))
        .expect("semantic registry must remain readable");
    let synthetic = "WSM-NOOP-150";
    assert!(
        !registry.contains(synthetic),
        "#150 synthetic machine mnemonic leaked into semantic registry"
    );
}
