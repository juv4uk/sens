//! #1096 acceptance witnesses for globally reserved bare 8-bit SID literals.
//!
//! These tests exercise the public evaluator boundary only. Semantic meaning
//! remains owned by the Canon/function table; the test does not add a host map.

use my_lisp::{eval_program, ErrorKind, Session};

#[test]
fn bare_sids_dispatch_existing_canon_and_necessary_forms_without_binary_descriptor() {
    let source = r#"
        (00001001 make-pair
          (00001000 (left right)
            (00000100 left (00000100 right ()))))
        (00000101 (make-pair 1 2))
    "#;

    let mut session = Session::default();
    let result = eval_program(source, &mut session)
        .expect("bare 8-bit SID list heads should execute their admitted meaning");

    assert_eq!(result.value.to_string(), "1");
}

#[test]
fn bare_arithmetic_sid_and_surface_name_reach_the_same_admitted_meaning() {
    let mut sid_session = Session::default();
    let sid = eval_program("(00001100 2 3)", &mut sid_session)
        .expect("SID 00001100 should invoke the admitted + meaning");

    let mut surface_session = Session::default();
    let surface = eval_program("(+ 2 3)", &mut surface_session)
        .expect("surface + should invoke the same admitted meaning");

    assert_eq!(sid.value.to_string(), "5");
    assert_eq!(sid.value, surface.value);
}

#[test]
fn bare_sid_zero_is_not_decimal_zero_or_empty_list() {
    let mut session = Session::default();
    let result = eval_program("00000000", &mut session)
        .expect("bare 00000000 should be a first-class SID value");

    assert_eq!(result.value.to_string(), "00000000");
}

#[test]
fn unadmitted_bare_sid_is_a_value_but_does_not_mint_callable_meaning() {
    let mut value_session = Session::default();
    let value = eval_program("11111111", &mut value_session)
        .expect("bare 8-bit SID should remain a first-class SID value");
    assert_eq!(value.value.to_string(), "11111111");

    let mut call_session = Session::default();
    let error = eval_program("(11111111)", &mut call_session)
        .expect_err("unadmitted SID invocation must fail closed");

    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("unknown semantic callable SID: 11111111"));
}
