use sens::{eval_program, load_core_library, parse, Session};

#[test]
fn rust_semantic_registry_generator_is_valid_lisp() {
    parse(include_str!("../../../scripts/generate-rust-semantic-registry.lisp"))
        .expect("Rust semantic-registry generator must remain valid Lisp source");
}


#[test]
fn decimal_values_do_not_mint_semantic_identity() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    let result = eval_program(
        "(equal? 00001100 12)",
        &mut session,
    )
    .expect("Binary-vs-decimal distinction must be executable")
    .value
    .to_string();

    assert_eq!(
        result,
        "(0)",
        "decimal 12 must remain ordinary numeric data, not mint Binary SID 00001100"
    );
}

#[test]
fn primitive_budget_audit_has_no_decimal_identity_shadow() {
    let audit = include_str!("../../../contracts/primitive-budget-audit-734.lisp");
    assert!(
        !audit.contains("(index ."),
        "primitive budget audit must not duplicate Binary SID identity as a decimal index"
    );
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
