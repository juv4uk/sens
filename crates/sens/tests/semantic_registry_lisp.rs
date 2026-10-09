use sens::parse;

#[test]
fn rust_semantic_registry_generator_is_valid_lisp() {
    parse(include_str!("../../../scripts/generate-rust-semantic-registry.lisp"))
        .expect("Rust semantic-registry generator must remain valid Lisp source");
}

#[test]
fn former_binary_header_does_not_change_decimal_reading() {
    let expressions = sens::parse("(binary 8) 00000102")
        .expect("ordinary parser must not have a binary reader mode");
    assert!(matches!(expressions[1].kind, sens::ExprKind::Number(value, _) if value == 102.0));
}

#[test]
fn registry_handoff_contract_names_authority_without_copying_rows() {
    let contract = include_str!("../../../contracts/semantic-registry-handoff-996.lisp");
    parse(contract).expect("registry handoff contract must remain valid Lisp data");

    assert!(contract.contains("(authority \"lib/surface/semantic-registry.lisp\")"));
    assert!(contract.contains("(revision-pin git-commit-containing-authority)"));
    assert!(contract.contains("(content-digest sha256-utf8-source)"));
    assert!(contract.contains("decimal-sid-shadow-table"));
    assert!(contract.contains("string-sid-shadow-table"));
    assert!(
        !contract.contains("00000001"),
        "handoff policy must not become a second semantic registry"
    );
}
