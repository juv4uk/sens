//! Smoke test for canonical `sens` crate import.
use sens::{eval_program, Session};

#[test]
fn sens_crate_evaluates_basic_expressions() {
    let mut session = Session::default();
    let result = eval_program("(+ 40 2)", &mut session).expect("should evaluate");
    assert_eq!(result.value.to_string(), "42");
}

#[test]
fn sens_macro_constructs_sens8_identity() {
    let s = sens::sens!(00000001);
    assert_eq!(s.to_string(), "00000001");
}
