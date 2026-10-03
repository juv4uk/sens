use sens::{eval_program, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn d5_plus_surfaces_execute_the_same_exact_mechanism() {
    assert_eq!(eval("(+ 1 2 3)"), "6");
    assert_eq!(eval("(plus 1 2 3)"), "6");
    assert_eq!(eval("(додати 1 2 3)"), "6");
    assert_eq!(eval("(yoga 1 2 3)"), "6");
}

#[test]
fn d5_arithmetic_owner_coordinates_preserve_exact_results() {
    assert_eq!(eval("(- 7 2 1)"), "4");
    assert_eq!(eval("(* 2 3 4)"), "24");
    assert_eq!(eval("(/ 6 3)"), "2");
    assert_eq!(eval("(quotient 6 3)"), "2");
    assert_eq!(eval("(+ (/ 1 3) (/ 1 6))"), "1/2");
}

#[test]
fn admitted_d5_identity_without_runtime_mechanism_fails_closed() {
    let mut session = Session::default();
    let error = eval_program("(setq (quote x) 1)", &mut session)
        .expect_err("SETQ is a D5 identity but its runtime law is not implemented in this slice");
    assert!(
        error.to_string().contains("domain identity has no admitted value-call mechanism"),
        "unexpected error: {error:?}"
    );
}
