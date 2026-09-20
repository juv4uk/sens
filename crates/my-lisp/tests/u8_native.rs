use my_lisp::{eval_program, load_core_library, ErrorKind, Session};

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core + u8 library");
    session
}

fn eval(source: &str) -> Result<String, my_lisp::LanguageError> {
    let mut session = session();
    Ok(eval_program(source, &mut session)?.value.to_string())
}

fn eval_error(source: &str) -> my_lisp::LanguageError {
    let mut session = session();
    eval_program(source, &mut session).expect_err("source should fail")
}

#[test]
fn binary_is_the_u8_domain_without_a_second_value_representation() {
    assert_eq!(eval("(binary 8) (u8? 00000101)").unwrap(), "істина");
    assert_eq!(eval("(binary 8) (u8 00000101)").unwrap(), "00000101");
    assert_eq!(eval("(binary 8) (u8->binary 00000101)").unwrap(), "00000101");
}

#[test]
fn integer_to_u8_requires_explicit_conversion_and_preserves_width() {
    assert_eq!(eval("(integer->u8 0)").unwrap(), "00000000");
    assert_eq!(eval("(integer->u8 1)").unwrap(), "00000001");
    assert_eq!(eval("(integer->u8 5)").unwrap(), "00000101");
    assert_eq!(eval("(integer->u8 254)").unwrap(), "11111110");
    assert_eq!(eval("(integer->u8 255)").unwrap(), "11111111");
    assert_eq!(eval("(u8->integer (integer->u8 168))").unwrap(), "168");
    assert_eq!(eval("(u8? 168)").unwrap(), "()");
}

#[test]
fn u8_values_compare_as_language_values() {
    assert_eq!(eval("(binary 8) (eq 00000101 00000101)").unwrap(), "істина");
    assert_eq!(eval("(eq (integer->u8 5) (integer->u8 5))").unwrap(), "істина");
    assert_eq!(eval("(eq (integer->u8 5) (integer->u8 6))").unwrap(), "()");
}

#[test]
fn semantic_id_10101000_travels_as_lisp_u8_without_decimal_authority() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core + u8 library");
    eval_program(
        include_str!("../../../lib/surface/semantic-registry-api.lisp"),
        &mut session,
    )
    .expect("Lisp-owned semantic registry API");

    let registry_source = include_str!("../../../lib/surface/semantic-registry.lisp");
    let program = format!(
        "(binary 8) (let ((registry (semantic-registry-read-source {}))) (semantic-registry-surface-name (quote en) (semantic-registry-row-in registry (u8 10101000))))",
        format!("{registry_source:?}")
    );
    let result = eval_program(&program, &mut session)
        .expect("Binary semantic ID should resolve through the Lisp registry")
        .value
        .to_string();
    assert_eq!(result, "invoke");

    let round_trip = eval_program(
        "(semantic-registry-round-trip (u8 10101000))",
        &mut session,
    )
    .expect("u8 semantic ID should read/print/read through Lisp")
    .value
    .to_string();
    assert_eq!(round_trip, "10101000");
}

#[test]
fn printed_u8_round_trips_through_lisp_read() {
    assert_eq!(
        eval(r#"(binary 8) (eval (car (cdr (read-all "(binary 8) 00000101"))))"#).unwrap(),
        "00000101"
    );
}

#[test]
fn bitwise_operations_are_fixed_width_and_self_hosted() {
    assert_eq!(eval("(binary 8) (u8-and 10101000 00001111)").unwrap(), "00001000");
    assert_eq!(eval("(binary 8) (u8-or 10000000 00001111)").unwrap(), "10001111");
    assert_eq!(eval("(binary 8) (u8-xor 10101000 11111111)").unwrap(), "01010111");
    assert_eq!(eval("(binary 8) (u8-not 00000101)").unwrap(), "11111010");
    assert_eq!(eval("(binary 8) (u8-shl 00000001 0)").unwrap(), "00000001");
    assert_eq!(eval("(binary 8) (u8-shl 00000001 1)").unwrap(), "00000010");
    assert_eq!(eval("(binary 8) (u8-shl 00000001 7)").unwrap(), "10000000");
    assert_eq!(eval("(binary 8) (u8-shl 10000000 1)").unwrap(), "00000000");
    assert_eq!(eval("(binary 8) (u8-shr 10000000 7)").unwrap(), "00000001");
}

#[test]
fn u8_arithmetic_rejects_overflow_and_underflow() {
    assert_eq!(eval("(binary 8) (u8-add 00000001 00000010)").unwrap(), "00000011");
    assert_eq!(eval("(binary 8) (u8-sub 00000101 00000001)").unwrap(), "00000100");

    let overflow = eval_error("(binary 8) (u8-add 11111111 00000001)");
    assert_eq!(overflow.kind, ErrorKind::NumericOverflow);

    let underflow = eval_error("(binary 8) (u8-sub 00000000 00000001)");
    assert_eq!(underflow.kind, ErrorKind::NumericOverflow);
}

#[test]
fn u8_rejects_invalid_conversions_and_shift_counts() {
    let too_large = eval_error("(binary 8) (integer->u8 256)");
    assert_eq!(too_large.kind, ErrorKind::NumericOverflow);

    let negative = eval_error("(binary 8) (integer->u8 -1)");
    assert_eq!(negative.kind, ErrorKind::NumericOverflow);

    let wrong_width = eval_error("(u8->integer 5)");
    assert_eq!(wrong_width.kind, ErrorKind::Type);

    let bad_shift = eval_error("(binary 8) (u8-shl 00000001 8)");
    assert_eq!(bad_shift.kind, ErrorKind::InvalidForm);

    let negative_shift = eval_error("(binary 8) (u8-shl 00000001 -1)");
    assert_eq!(negative_shift.kind, ErrorKind::InvalidForm);
}


#[test]
fn u8_boundary_audit_keeps_raw_transport_distinct() {
    let audit = include_str!("../../../contracts/u8-boundary-audit-954.lisp");
    my_lisp::parse(audit).expect("u8 boundary audit must remain readable Lisp data");

    for required in [
        "(classification language-value)",
        "(classification semantic-binary-identity-projection)",
        "(classification raw-host-mechanism)",
        "(classification machine-mechanism)",
        "(classification opaque-semantic-id-transport)",
        "(name lisp-u8)",
        "(current-representation binary-width-8)",
    ] {
        assert!(
            audit.contains(required),
            "u8 boundary audit lost required classification: {required}"
        );
    }

    assert!(
        audit.contains("(name file-raw-bytes)") && audit.contains("(action retain)"),
        "raw file-byte transport must not be silently redefined as Lisp u8 semantics"
    );
    assert!(
        audit.contains("(name kernel-c-abi-semantic-id)")
            && audit.contains("(language-u8-domain no)"),
        "opaque C ABI SID transport must remain distinct from the Lisp u8 value domain"
    );
}
