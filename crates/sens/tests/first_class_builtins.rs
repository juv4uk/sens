//! Acceptance matrix for contract 2.1 — first-class builtins.
//!
//! PROPOSAL: docs/PROPOSAL-FIRST-CLASS-BUILTINS.md (v2, c736d2e).
//! These tests are the §4 acceptance matrix. They are `#[ignore]`d until
//! the 2.1 implementation lands; each `#[ignore]` removed = one matrix
//! row proven. The WSM-24 geometry driver (`mylisp/`) is the §8.8 final
//! acceptance run once all rows pass un-ignored.
//!
//! Ігноровані до реалізації 2.1; знятий атрибут = доведений рядок матриці.

use sens::{eval_program, ErrorKind, Session};

fn session_with_core() -> Session {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("core.my should preload cleanly");
    session
}

fn eval_source(source: &str) -> String {
    let result = eval_program(source, &mut session_with_core()).expect("eval should succeed");
    result.value.to_string()
}

#[test]

fn builtins_are_callable_in_head_position_unchanged() {
    assert_eq!(eval_source("(+ 1 2)"), "3");
}

#[test]

fn def_f_plus_then_call_proves_first_classness() {
    assert_eq!(eval_source("(def f +) (f 20 22)"), "42");
}

#[test]

fn reduce_over_builtin_add() {
    assert_eq!(eval_source("(reduce + 0 (list 1 2 3))"), "6");
}

#[test]

fn map_over_builtin_car() {
    assert_eq!(eval_source("(map car (quote ((1 2) (3 4))))"), "(1 3)");
}

#[test]

fn builtin_as_higher_order_argument() {
    assert_eq!(eval_source("((lambda (f) (f 2 3)) +)"), "5");
}

#[test]

fn select_operator_from_list() {
    assert_eq!(eval_source("((car (list + -)) 8 2)"), "10");
}

#[test]

fn applying_a_non_callable_is_a_named_error() {
    let err = eval_program("(42 1 2)", &mut session_with_core()).expect_err("42 is not callable");
    assert_eq!(err.kind, ErrorKind::Type);
}

#[test]

fn special_forms_are_not_values() {
    // `(def q quote)` must NOT make quote callable as a value; per
    // contract 2.1 special forms keep their syntax-only status. The exact
    // error kind is implementation-defined, but it MUST be an error,
    // never silent success.
    let outcome = eval_program("(def q quote) (q (quote x))", &mut session_with_core());
    assert!(
        outcome.is_err(),
        "special forms must not become callable values"
    );
}

#[test]

fn lexical_shadowing_of_builtin_name() {
    assert_eq!(
        eval_source("((lambda (+) (+ 2 3)) (lambda (a b) (* a b)))"),
        "6"
    );
}

