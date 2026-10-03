use sens::{eval_program, load_core_library, parse, Session};

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
    let program = format!("(semantic-registry-self-hosted-witness {registry_source:?})");
    let result = eval_program(&program, &mut session)
        .expect("Lisp-owned semantic registry witness should evaluate")
        .value
        .to_string();

    assert_eq!(
        result,
        r#"(256 "00000001" quote "00000001" "10101000" "00000101" "11111111" (11111111 (en ()) (ук ()) (укр ()) (sa ()) (sym ())) "10101000" (1))"#
    );
}

#[test]
fn lisp_registry_api_accepts_headerless_canonical_rows() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(
        include_str!("../../../lib/surface/semantic-registry-api.lisp"),
        &mut session,
    )
    .expect("Lisp-owned semantic registry API should load");

    let registry_source = include_str!("../../../lib/surface/semantic-registry.lisp");
    let result = eval_program(
        &format!("(length (semantic-registry-rows (semantic-registry-read-source {registry_source:?})))"),
        &mut session,
    )
    .expect("headerless Canon rows should load")
    .value
    .to_string();

    assert_eq!(result, "256");
}

#[test]
fn rust_semantic_registry_generator_is_valid_lisp() {
    parse(include_str!("../../../scripts/generate-rust-semantic-registry.lisp"))
        .expect("Rust semantic-registry generator must remain valid Lisp source");
}



#[test]
fn exact_domain_registry_source_and_generator_are_valid_lisp() {
    parse(include_str!("../../../lib/surface/domain-registry.lisp"))
        .expect("exact-domain surface registry must remain valid Lisp data");
    parse(include_str!("../../../scripts/generate-rust-domain-registry.lisp"))
        .expect("exact-domain Rust projection generator must remain valid Lisp source");
}

#[test]
fn exact_domain_projection_has_no_legacy_byte_axis() {
    let source = include_str!("../../../lib/surface/domain-registry.lisp");
    let generated = include_str!("../src/domain_surface_registry_generated.rs");

    assert!(
        source.contains("(#b11 \"001\"") && source.contains("(#b100 \"0010\""),
        "authority must state exact domain width in binary and exact bits explicitly"
    );
    assert!(
        !generated.contains("semantic_id:"),
        "exact-domain projection must not carry legacy semantic_id bytes"
    );
    assert!(
        generated.contains("width: 3") && generated.contains("width: 4"),
        "generated projection must preserve exact domain width"
    );
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
fn shorter_bit_only_spelling_remains_ordinary_numeric_data() {
    let mut session = Session::default();
    let rendered = eval_program("000101", &mut session)
        .expect("shorter bit-only spelling must remain under ordinary numeric rules")
        .value
        .to_string();
    assert_eq!(
        rendered, "101",
        "only exact eight-bit bare 0/1 spellings are reserved as SID identity"
    );
}

#[test]
fn former_binary_header_does_not_change_decimal_reading() {
    let expressions = sens::parse("(binary 8) 00000102")
        .expect("ordinary parser must not have a binary reader mode");
    assert!(matches!(expressions[1].kind, sens::ExprKind::Number(value, _) if value == 102.0));
}


#[test]
fn full_binary_registry_handoff_is_lisp_owned_and_digest_pinned() {
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
    let program = format!("(semantic-registry-handoff-witness {registry_source:?})");
    let rendered = eval_program(&program, &mut session)
        .expect("Lisp-owned registry handoff should evaluate")
        .value
        .to_string();

    let digest = sens::sha256_source(registry_source.as_bytes())
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();

    assert!(
        rendered.starts_with("(semantic-registry-handoff/1 "),
        "handoff must remain an explicit versioned Lisp record: {rendered}"
    );
    assert!(
        rendered.contains(&format!("(source-digest \"{digest}\")")),
        "Lisp handoff digest must identify the exact canonical source bytes"
    );
    assert!(
        rendered.contains("(row-count 256)"),
        "handoff must report every current canonical semantic row"
    );
    assert!(
        rendered.contains("(canonical-rows (00000000 "),
        "handoff must expose the parsed canonical rows beginning with Binary SID values"
    );
    assert!(
        rendered.contains("(10101000 (en invoke)"),
        "handoff must preserve the invoke row as Binary identity data"
    );
    assert!(
        rendered.contains("(11111111 (en ())"),
        "handoff must preserve the current canonical registry tail as Binary identity data"
    );
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
