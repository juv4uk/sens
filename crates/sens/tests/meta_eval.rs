//! Exercises lib/meta-eval.my — the metacircular evaluator written in
//! sens itself (see PLAN.md, Krok 9, item 1). Loads lib/core.my (for
//! `second`/`third`) and lib/meta-eval.my into one session, then runs
//! `(my-eval (read "...") env)` the same way a user would from a REPL.
//! Pereviriaie lib/meta-eval.my — metatsyrkuliarnyi evaluator, napysanyi
//! samoiu sens (dyv. PLAN.md, Krok 9, punkt 1). Zavantazhuie lib/core.my
//! (zarady `second`/`third`) i lib/meta-eval.my v odnu sesiiu, todi
//! zapuskaie `(my-eval (read "...") env)` tak samo, yak korystuvach z REPL.
//! Prüft lib/meta-eval.my — den metazirkulären Evaluator, geschrieben in
//! sens selbst (siehe PLAN.md, Schritt 9, Punkt 1). Lädt lib/core.my
//! (wegen `second`/`third`) und lib/meta-eval.my in eine Sitzung, führt
//! dann `(my-eval (read "...") env)` genauso aus wie ein Nutzer aus der REPL.

use sens::{eval_program, Session};

fn eval_meta(expr_source: &str, env_source: &str) -> String {
    let mut session = Session::default();
    sens::load_core_library(&mut session).unwrap();
    sens::load_meta_evaluator_library(&mut session).unwrap();
    let source = format!(
        r#"(my-eval (read "{}") {})"#,
        expr_source.replace('\\', "\\\\").replace('"', "\\\""),
        env_source
    );
    eval_program(&source, &mut session)
        .unwrap()
        .value
        .to_string()
}

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
    eval_program(&source, &mut session)
        .unwrap()
        .value
        .to_string()
}

#[test]
fn self_evaluates_numbers_and_symbols_not_bound_in_env() {
    assert_eq!(eval_meta("42", "(quote ())"), "42");
    assert_eq!(eval_meta("t", "(quote ())"), "t");
}

#[test]
fn quote_returns_data_unevaluated() {
    assert_eq!(eval_meta("(quote radio)", "(quote ())"), "radio");
}

#[test]
fn arithmetic_dispatches_to_the_real_primitives() {
    assert_eq!(eval_meta("(+ 1 2)", "(quote ())"), "3");
    assert_eq!(eval_meta("(* 3 4)", "(quote ())"), "12");
}

#[test]
fn cond_picks_the_first_truthy_clause() {
    assert_eq!(eval_meta("(cond (() 1) (t 2))", "(quote ())"), "2");
}

#[test]
fn list_primitives_dispatch_to_the_real_primitives() {
    assert_eq!(
        eval_meta("(cons 1 (cons 2 (quote ())))", "(quote ())"),
        "(1 2)"
    );
    assert_eq!(eval_meta("(car (cons 1 2))", "(quote ())"), "1");
}

#[test]
fn lambda_application_binds_parameters_and_evaluates_the_body() {
    assert_eq!(eval_meta("((lambda (x) (+ x 1)) 5)", "(quote ())"), "6");
}

#[test]
fn multi_expression_lambda_bodies_evaluate_in_sequence_returning_the_last() {
    assert_eq!(
        eval_meta("((lambda (x y) (+ x y) (* x y)) 3 4)", "(quote ())"),
        "12"
    );
}

#[test]
fn closures_capture_free_variables_from_the_calling_env() {
    assert_eq!(
        eval_meta(
            "((lambda (y) (+ x y)) 10)",
            "(cons (cons (quote x) 5) (quote ()))"
        ),
        "15"
    );
}

#[test]
fn higher_order_functions_pass_a_closure_as_an_argument() {
    assert_eq!(
        eval_meta(
            "((lambda (f x) (f x)) (lambda (n) (* n n)) 6)",
            "(quote ())"
        ),
        "36"
    );
}

#[test]
fn bare_symbol_lambda_list_binds_all_arguments() {
    let expr = "((lambda args args) 1 2 3 4)";
    let via_meta = eval_meta(expr, "(quote ())");

    let mut native = Session::default();
    let via_native = eval_program(expr, &mut native)
        .expect("native evaluator should support an all-rest lambda parameter")
        .value
        .to_string();

    assert_eq!(via_meta, "(1 2 3 4)");
    assert_eq!(via_native, "(1 2 3 4)");
}

#[test]
fn dotted_lambda_list_binds_remaining_arguments_as_rest_list() {
    let expr = "((lambda (x y . rest) rest) 10 20 30 40)";
    let via_meta = eval_meta(expr, "(quote ())");

    let mut native = Session::default();
    let via_native = eval_program(expr, &mut native)
        .expect("native evaluator should support a dotted rest parameter")
        .value
        .to_string();

    assert_eq!(via_meta, "(30 40)");
    assert_eq!(via_native, "(30 40)");
}

#[test]
fn def_extends_the_environment_visible_to_later_top_level_forms() {
    assert_eq!(eval_meta_program("(def x 10) (def y (+ x 5))", "y"), "15");
}

#[test]
fn def_can_bind_a_lambda_callable_from_a_later_top_level_form() {
    assert_eq!(
        eval_meta_program("(def square (lambda (n) (* n n))) (square 6)", "(square 6)"),
        "36"
    );
}

#[test]
fn defmacro_expands_before_evaluating_using_unevaluated_argument_forms() {
    assert_eq!(
        eval_meta_program(
            "(defmacro my-if (test then else) \
             (cons (quote cond) (cons (cons test (cons then (quote ()))) \
                                (cons (cons 't (cons else (quote ()))) (quote ())))))",
            "(my-if t (quote yes) (quote no))"
        ),
        "yes"
    );
}

#[test]
fn loads_a_real_verbatim_slice_of_lib_core_my_and_runs_it_through_my_eval() {
    let core_slice = r#"
(def identity (lambda (value) value))
(def not (lambda (value) (cond (value (quote ())) (t t))))
(def pair (lambda (left right) (cons left (cons right (quote ())))))
(def second (lambda (values) (car (cdr values))))
(def third (lambda (values) (car (cdr (cdr values)))))
"#;
    assert_eq!(
        eval_meta_program(core_slice, "(second (quote (a b c)))"),
        "b"
    );
    assert_eq!(
        eval_meta_program(core_slice, "(third (quote (a b c)))"),
        "c"
    );
    assert_eq!(eval_meta_program(core_slice, "(not (quote ()))"), "t");
    assert_eq!(
        eval_meta_program(core_slice, "(identity (quote radio))"),
        "radio"
    );
}

#[test]
fn self_recursive_top_level_def_sees_its_own_binding() {
    assert_eq!(
        eval_meta_program(
            "(def count-down (lambda (n) (cond ((eq? n 0) (quote done)) (t (count-down (- n 1))))))",
            "(count-down 20)"
        ),
        "done"
    );
}

#[test]
fn recursive_factorial_matches_native_language_meaning() {
    let program = "(def fact (lambda (n) (cond ((eq? n 0) 1) (t (* n (fact (- n 1)))))))";
    let via_meta = eval_meta_program(program, "(fact 6)");

    let mut native = Session::default();
    let native_source = format!("{program} (fact 6)");
    let via_native = eval_program(&native_source, &mut native)
        .expect("native evaluator should execute the same recursive definition")
        .value
        .to_string();

    assert_eq!(via_meta, "720");
    assert_eq!(via_native, "720");
}
