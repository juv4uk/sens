//! First-class function law: the value is the exact Function8.
//!
//! Human spellings may lower at the call boundary, but passing, storing,
//! selecting, and invoking a function as data uses its exact eight bits.

use sens::{eval_program, ErrorKind, Session};

fn session_with_core() -> Session {
    let mut session = Session::default();
    sens::load_core_library(&mut session)
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
    assert_eq!(eval_source("(def f 00001100) (f 20 22)"), "42");
}

#[test]

fn reduce_over_builtin_add() {
    assert_eq!(eval_source("(reduce 00001100 0 (list 1 2 3))"), "6");
}

#[test]

fn map_over_builtin_car() {
    assert_eq!(eval_source("(map 00000101 (00000001 ((1 2) (3 4))))"), "(1 3)");
}

#[test]

fn builtin_as_higher_order_argument() {
    assert_eq!(eval_source("((lambda (f) (f 2 3)) 00001100)"), "5");
}

#[test]

fn select_operator_from_list() {
    assert_eq!(eval_source("((00000101 (list 00001100 00001101)) 8 2)"), "10");
}

#[test]

fn applying_a_non_callable_is_a_named_error() {
    let err = eval_program("(42 1 2)", &mut session_with_core()).expect_err("42 is not callable");
    assert_eq!(err.kind, ErrorKind::Type);
}

#[test]

fn special_forms_are_not_values() {
    // The exact quote Function8 is a value, but ordinary value invocation must
    // not erase its special evaluation rule.
    let outcome = eval_program(
        "(def q 00000001) (q (00000001 x))",
        &mut session_with_core(),
    );
    assert!(
        outcome.is_err(),
        "special forms must not become callable values"
    );
}
