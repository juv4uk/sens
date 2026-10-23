mod common;

use sens::{eval_program, load_core_library, ErrorKind, Session};

fn meta_session() -> Session {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    common::load_meta_evaluator_library(&mut session).expect("meta-eval bootstrap");
    session
}

fn meta_eval_program(program: &str, probe: &str) -> String {
    let mut session = meta_session();
    let source = format!(
        "(обчислити-мета-вираз (quote {probe}) (перше (обчислити-послідовність-форм (quote ({program})) (quote ()))))"
    );
    eval_program(&source, &mut session)
        .unwrap_or_else(|error| panic!("host failure while probing meta program: {error}"))
        .value
        .to_string()
}

fn native_value(program: &str, probe: &str) -> String {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    eval_program(&format!("{program}\n{probe}"), &mut session)
        .unwrap_or_else(|error| panic!("reference evaluator failed: {error}"))
        .value
        .to_string()
}

fn native_error_kind(program: &str, probe: &str) -> ErrorKind {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    eval_program(&format!("{program}\n{probe}"), &mut session)
        .expect_err("reference program must fail")
        .kind
}

#[test]
fn later_binding_in_the_same_definition_frame_is_visible() {
    let program =
        "(визначити перша-функція (функція () пізніша-функція)) (визначити пізніша-функція 42)";
    assert_eq!(native_value(program, "(перша-функція)"), "42");
    assert_eq!(meta_eval_program(program, "(перша-функція)"), "42");
}

#[test]
fn later_replacement_in_the_same_definition_frame_is_visible() {
    let program = "(визначити пізніша-функція 1) (визначити перша-функція (функція () пізніша-функція)) (визначити пізніша-функція 2)";
    assert_eq!(native_value(program, "(перша-функція)"), "2");
    assert_eq!(meta_eval_program(program, "(перша-функція)"), "2");
}

#[test]
fn one_way_later_lambda_binding_is_visible_without_inventing_an_scc() {
    let program = "(визначити перша-функція (функція (значення) (пізніша-функція значення))) (визначити пізніша-функція (функція (значення) значення))";
    assert_eq!(native_value(program, "(перша-функція 42)"), "42");
    assert_eq!(meta_eval_program(program, "(перша-функція 42)"), "42");

    let closure = meta_eval_program(program, "перша-функція");
    assert!(
        closure.starts_with("(recursive-closure перша-функція "),
        "one-way dependency must remain outside a recursive SCC, got {closure}"
    );
}

#[test]
fn call_before_the_later_binding_remains_unresolved() {
    let program = "(визначити перша-функція (функція () (пізніша-функція)))";
    assert_eq!(
        native_error_kind(program, "(перша-функція)"),
        ErrorKind::UnknownSymbol
    );
    assert_eq!(
        meta_eval_program(program, "(перша-функція)"),
        "(error unbound-symbol пізніша-функція)"
    );
}

#[test]
fn lexical_parameter_shadowing_still_beats_the_shared_definition_frame() {
    let program = "(визначити пізніша-функція 1) (визначити перша-функція (функція (пізніша-функція) пізніша-функція)) (визначити пізніша-функція 2)";
    assert_eq!(native_value(program, "(перша-функція 9)"), "9");
    assert_eq!(meta_eval_program(program, "(перша-функція 9)"), "9");
}

#[test]
fn nested_closure_keeps_its_child_binding_while_parent_frame_keeps_growing() {
    let program = "(визначити створити-функцію (функція (значення) (функція () значення))) (визначити збережене-замикання (створити-функцію 7)) (визначити пізніша-функція 42)";
    assert_eq!(native_value(program, "(збережене-замикання)"), "7");
    assert_eq!(meta_eval_program(program, "(збережене-замикання)"), "7");
}
