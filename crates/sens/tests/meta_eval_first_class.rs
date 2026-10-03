//! Contract-2.1 witness for the main metacircular evaluator.
//! The expressions below are copied from the already-existing native
//! first-class-builtin acceptance matrix; this test does not invent a new
//! semantic target for the Lisp evaluator.

use sens::{eval_program, Session};

const HIGHER_ORDER_BUILTIN: &str = "((lambda (f) (f 2 3)) 00001100)";

fn eval_native(expr: &str) -> String {
    let mut session = Session::default();
    eval_program(expr, &mut session)
        .unwrap_or_else(|e| panic!("native evaluator failed: {e}\nexpr: {expr}"))
        .value
        .to_string()
}

fn eval_via_meta(expr: &str) -> String {
    let mut session = Session::default();
    sens::load_core_library(&mut session)
        .expect("core.my should load");
    sens::load_meta_evaluator_library(&mut session)
        .expect("main metacircular evaluator should load");

    let escaped = expr.replace('\\', "\\\\").replace('"', "\\\"");
    let source = format!(r#"(my-eval (read "{escaped}") (quote ()))"#);
    eval_program(&source, &mut session)
        .unwrap_or_else(|e| panic!("main meta-eval failed: {e}\nexpr: {expr}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn witness_expressions_are_existing_contract_21_acceptance_cases() {
    let matrix = include_str!("first_class_builtins.rs");
    assert!(matrix.contains(HIGHER_ORDER_BUILTIN));
}

#[test]
fn main_metacircular_evaluator_accepts_builtin_as_higher_order_value() {
    assert_eq!(eval_native(HIGHER_ORDER_BUILTIN), "5");
    assert_eq!(eval_via_meta(HIGHER_ORDER_BUILTIN), "5");
}
