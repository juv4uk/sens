//! Rust перевіряє тільки механізм діагностування помилки середовищем виконання.
//! Арифметичні рівності й очікуваний PASS визначає Lisp-свідок у tests/semantic.
use sens::{eval_program, load_core_library, ErrorKind, Session};

fn core_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("SENS core must load");
    session
}

#[test]
fn exact_arithmetic_laws_are_judged_by_lisp() {
    let source = include_str!("../../../tests/semantic/exact-arithmetic-laws.lisp");
    let result = eval_program(source, &mut core_session())
        .expect("Lisp-owned exact arithmetic laws must execute")
        .value
        .to_string();

    assert!(
        result.starts_with("(exact-arithmetic-law (status pass)"),
        "Lisp witness rejected the runtime's arithmetic results: {result}"
    );
}

#[test]
fn rust_runtime_classifies_zero_reciprocal_as_division_by_zero() {
    // Це тест Rust-механізму категоризації помилок, не альтернативний
    // математичний оракул. Самі арифметичні закони перевіряє Lisp-свідок.
    let mut session = core_session();
    let error = eval_program("(обернене число-нуль)", &mut session)
        .expect_err("the runtime must reject a reciprocal of zero");
    assert_eq!(error.kind, ErrorKind::DivisionByZero);
}
