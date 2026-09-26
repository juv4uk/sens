use sens::{eval_program, ErrorKind, Session};

fn meta_session() -> Session {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("core bootstrap");
    sens::load_meta_evaluator_library(&mut session)
        .expect("meta-eval should load under Contract 6.0");
    session
}

fn meta_eval(expr: &str) -> String {
    let mut session = meta_session();
    let escaped = expr.replace('\\', "\\\\").replace('"', "\\\"");
    eval_program(
        &format!(r#"(my-eval (read "{escaped}") (quote ()))"#),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("meta-eval host failure for {expr}: {error}"))
    .value
    .to_string()
}

fn meta_eval_with_hostile_binding(expr: &str, name: &str) -> String {
    let mut session = meta_session();
    let escaped = expr.replace('\\', "\\\\").replace('"', "\\\"");
    eval_program(
        &format!(
            r#"(my-eval (read "{escaped}") (list (cons (quote {name}) 99)))"#
        ),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("meta-eval hostile-env host failure for {expr}: {error}"))
    .value
    .to_string()
}

fn meta_program(program: &str) -> String {
    let mut session = meta_session();
    let escaped = program.replace('\\', "\\\\").replace('"', "\\\"");
    eval_program(
        &format!(
            r#"(cdr (my-eval-program (read-all "{escaped}") (quote ())))"#
        ),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("meta-eval program host failure for {program}: {error}"))
    .value
    .to_string()
}

#[test]
fn native_and_meta_reject_canon_lambda_binders() {
    for name in ["car", "перше", "ādi", "atom", "атом?", "aṇu"] {
        let source = format!("(lambda ({name}) {name})");

        let mut native = Session::default();
        let error = eval_program(&source, &mut native)
            .expect_err("native evaluator must reject a Canon parameter");
        assert_eq!(error.kind, ErrorKind::InvalidForm, "source: {source}");

        let meta = meta_eval(&source);
        assert!(
            meta.contains("error invalid-form") && meta.contains("canonical-parameter"),
            "meta-eval must reject {name}, got: {meta}"
        );
    }
}

#[test]
fn meta_top_level_def_cannot_create_canon_binding() {
    for name in ["car", "перше", "ādi", "cond", "за-умовою", "anukrama"] {
        let result = meta_program(&format!("(def {name} 42)"));
        assert_eq!(
            result,
            format!("(error invalid-form (canonical-name-immutable {name}))"),
            "Canon definition must be rejected: {name}"
        );
    }
}

#[test]
fn hostile_meta_environment_cannot_retarget_canon_resolution() {
    for (name, call) in [
        ("car", "(car (quote (a b)))"),
        ("перше", "(перше (quote (a b)))"),
        ("ādi", "(ādi (quote (a b)))"),
    ] {
        assert_eq!(
            meta_eval_with_hostile_binding(call, name),
            "a",
            "hostile alist must not retarget {name}"
        );
    }
}

#[test]
fn noncanon_shadowing_survives_in_meta_eval() {
    assert_eq!(
        meta_eval("((lambda (+) (+ 2 3)) (lambda (a b) (* a b)))"),
        "6"
    );
}
