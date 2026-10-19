//! Точна раціональна арифметика через ратифіковану українську проєкцію SENS.
//!
//! D5:10111 — «частка», D5:01010 — «додати», D5:01011 — «відняти»,
//! D5:10110 — «помножити». Колишні восьмибітні голови тут більше не
//! використовуються: математичний результат належить D24+.
//! Числа у виконуваних SENS-виразах записано десятково; раціональні
//! значення утворює сам evaluator, а не reader-літерали 1/3.

use sens::{eval_program, ErrorKind, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {}", error.render(source)))
        .value
        .to_string()
}

#[test]
fn sens_division_produces_exact_rational_instead_of_panicking() {
    assert_eq!(eval("(частка 1 3)"), "1/3");
    assert_eq!(eval("(частка 6 3)"), "2");
    assert_eq!(eval("(частка (частка 1 3) (частка 1 6))"), "2");
}

#[test]
fn sens_arithmetic_closes_over_exact_rationals() {
    assert_eq!(eval("(додати (частка 1 3) (частка 1 6))"), "1/2");
    assert_eq!(eval("(відняти (частка 1 10) (частка 1 10))"), "0");
    assert_eq!(eval("(помножити (частка 1 3) 3)"), "1");
    assert_eq!(
        eval("(частка (додати (частка 1 3) (частка 1 6)) (частка 1 2))"),
        "1"
    );
}

#[test]
fn sens_division_by_zero_fails_as_language_error_not_panic() {
    let mut session = Session::default();
    let source = "(частка 1 0)";
    let error = eval_program(source, &mut session)
        .expect_err("ділення на точний нуль має бути помилкою мови");
    assert_ne!(error.kind, ErrorKind::Parse);
}
