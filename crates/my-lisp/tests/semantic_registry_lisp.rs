use my_lisp::{eval_program, load_core_library, parse, Session};

#[test]
fn semantic_registry_is_read_and_queried_by_lisp_itself() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(
        include_str!("../../../lib/surface/semantic-registry-api.lisp"),
        &mut session,
    )
    .expect("Lisp-owned semantic registry API should load");
    eval_program(
        include_str!("../../../tests/fixtures/semantic-registry-self-hosted-witness.lisp"),
        &mut session,
    )
    .expect("Lisp-owned semantic registry witness should load");

    let registry_source = include_str!("../../../lib/surface/semantic-registry.lisp");
    let program = format!(
        "(semantic-registry-self-hosted-witness {})",
        format!("{registry_source:?}")
    );
    let result = eval_program(&program, &mut session)
        .expect("Lisp-owned semantic registry witness should evaluate")
        .value
        .to_string();

    assert_eq!(
        result,
        r#"((binary 8) 170 "00000001" quote "00000001" "10101000" "00000101" "11111111" () "10101000" (structural-relation same))"#
    );
}

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
        "(binary 8) (equal? 00001100 12)",
        &mut session,
    )
    .expect("Binary-vs-decimal distinction must be executable")
    .value
    .to_string();

    assert_eq!(
        result,
        "(structural-relation distinct)",
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
