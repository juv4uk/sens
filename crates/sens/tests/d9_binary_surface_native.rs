//! D9: український резидент двійковий не отримує викличність лише через identity.
//! SENS відхиляє точний D9:110110110, для якого немає допущеного механізму.
//! Історична W8:10101001 і D9:110110110 залишаються різними координатами.

use sens::{eval_parsed_expressions, Bit9, CoreD9, DomainIdentity, Expr, ExprKind, Session, Span};

#[test]
fn d9_binary_has_only_one_canonical_ukrainian_surface_and_no_decimal_resident() {
    const TABLE: &str = include_str!("../../../lib/domains/d9.lisp");
    const BINDINGS: &str = include_str!("../src/d9_definition_bindings_generated.rs");
    const ROW: &str = "(110110110 (ук двійковий) (укр двійковий) (san dvimāna) (en binary) (LISP BINARY) (sym ()))";
    const NUMBER_ROW: &str = "(110111001 (ук число-рядок) (укр число-рядок) (san saṅkhyā-śabda) (en number->string) (LISP NUMBER->STRING) (sym ()))";
    assert!(BINDINGS.contains("D9DefinitionBinding { bits: 0b110110110, names: &[\"двійковий\", \"dvimāna\", \"binary\", \"BINARY\"] }"), "test_id=D9-BINARY-RUST-PROJECTION expected=двійковий actual=stale");
    assert!(
        TABLE.contains(ROW),
        "test_id=D9-BINARY-SURFACE layer=canonical_table expected=D9:110110110 ukr=двійковий"
    );
    assert!(
        TABLE.contains(NUMBER_ROW),
        "test_id=D9-NUMBER-STRING layer=canonical_table expected=D9:110111001"
    );
    assert_eq!(
        TABLE.matches("(110110110 ").count(),
        1,
        "test_id=D9-BINARY-UNIQUE"
    );
    assert_eq!(
        TABLE.matches("(110111001 ").count(),
        1,
        "test_id=D9-NUMBER-STRING-UNIQUE"
    );
    assert!(
        !TABLE.contains("(ук десятковий)"),
        "test_id=D9-NO-DECIMAL-RESIDENT"
    );
    assert!(
        !TABLE.contains("(укр десятковий)"),
        "test_id=D9-NO-DECIMAL-RESIDENT-UKR"
    );
}

#[test]
fn d9_binary_resident_does_not_implicitly_become_callable() {
    let exact_identity = Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D9(CoreD9::from_word(
            Bit9::new(0b110110110).expect("exact D9 word"),
        ))),
        span: Span::default(),
    };
    let call = Expr {
        kind: ExprKind::List(vec![exact_identity].into()),
        span: Span::default(),
    };
    let error = eval_parsed_expressions(&[call], &mut Session::default())
        .expect_err("D9 residency alone must not grant callability");
    assert!(
        error
            .message
            .contains("not callable under its ratified law"),
        "unexpected fail-closed diagnostic: {error:?}"
    );
}
