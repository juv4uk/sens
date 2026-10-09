//! Canonical D1-adapted LET* bootstrap regression; no new host semantic.
use sens::{eval_program, Session};

fn bootstrap() -> Session {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("Lisp-owned bootstrap");
    session
}

fn result(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .expect("Lisp-owned LET* expression must execute")
        .value
        .to_string()
}

#[test]
fn surface_and_binary_letstar_evaluate_one_binding() {
    let mut session = bootstrap();
    assert_eq!(result(&mut session, "(let ((x (00000001 datum))) x)"), "datum");
    assert_eq!(result(&mut session, "(let* ((x (00000001 datum))) x)"), "datum");
    assert_eq!(
        result(&mut session, "(10011101 ((x (00000001 datum))) x)"),
        "datum",
    );
}

#[test]
fn binary_letstar_bindings_are_sequential_not_parallel() {
    let mut session = bootstrap();
    assert_eq!(
        result(&mut session, "(10011101 ((x (00000001 datum)) (y x)) y)"),
        "datum",
    );
}

#[test]
fn legacy_atom_data_must_not_be_assumed_to_be_a_typed_d1_bit() {
    let mut session = bootstrap();
    assert_eq!(result(&mut session, "(00000010 (00000001 ()))"), "()");
    assert_eq!(result(&mut session, "(00000010 (00000001 (a b)))"), "(0)");
    let typed_no = eval_program(
        "(00100010 (00000001 d1-left) (00000001 d1-right))",
        &mut session,
    )
    .expect("canonical EQUAL");
    assert_eq!(typed_no.value.as_predicate_bit(), Some(false));
}
