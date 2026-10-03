//! Environment semantic witnesses for the metacircular evaluator.
//! These tests isolate closure ownership, lexical shadowing,
//! and recursive group behavior.

use sens::{eval_program, Session};

fn eval_meta_program(program_source: &str, probe_source: &str) -> String {
    let mut session = Session::default();
    sens::load_core_library(&mut session).unwrap();
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

#[test]
fn mutually_recursive_group_keeps_bindings_inside_lisp_data() {
    let program = r#"
(def even? (lambda (n) (cond ((eq? n 0) t) (t (odd? (- n 1))))))
(def odd? (lambda (n) (cond ((eq? n 0) ()) (t (even? (- n 1))))))
"#;

    assert_eq!(eval_meta_program(program, "(even? 20)"), "t");
    assert_eq!(eval_meta_program(program, "(odd? 20)"), "()");
}
