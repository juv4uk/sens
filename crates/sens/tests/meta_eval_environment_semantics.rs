//! Environment semantic witnesses for the metacircular evaluator.
//! These tests isolate closure ownership, lexical shadowing,
//! and recursive group behavior.

use sens::{eval_program, Session};

fn eval_meta_program(program_source: &str, probe_source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    sens::load_meta_evaluator_library(&mut session).unwrap();
    let source = format!(
        r#"(let ((loaded (my-eval-program (read-all "{}") (quote ()))))
             (my-eval (read "{}") (car loaded)))"#,
        program_source.replace('\\', "\\\\").replace('"', "\\\""),
        probe_source.replace('\\', "\\\\").replace('"', "\\\""),
    );
    eval_program(&source, &mut session).unwrap().value.to_string()
}

#[test]
fn nested_lambda_preserves_lexical_environment_capture() {
    assert_eq!(eval_meta_program("", "((lambda (x) ((lambda (y) (+ x y)) 2)) 40)"), "42");
}

#[test]
fn inner_binding_shadows_outer_lexical_binding() {
    assert_eq!(eval_meta_program("", "((lambda (x) ((lambda (x) x) 2)) 1)"), "2");
}
