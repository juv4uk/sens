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
    // Surface names of table functions and a SENS code itself (00000010,
    // atom?) — none may become a lambda parameter.
    for name in ["car", "перше", "ādi", "00000010", "атом?", "aṇu"] {
        let source = format!("(lambda ({name}) {name})");

        let mut native = Session::default();
        // `match`, not `expect_err`: printing an accepted closure with Debug
        // walks its self-referencing environment and overflows the stack,
        // which hid this failure as an aborted test binary.
        match eval_program(&source, &mut native) {
            Ok(_) => panic!("native evaluator must reject a Canon parameter: {source}"),
            Err(error) => assert_eq!(error.kind, ErrorKind::InvalidForm, "source: {source}"),
        }

        let is_code = name.len() == 8 && name.bytes().all(|b| b == b'0' || b == b'1');
        let reason = if is_code { "non-symbol-parameter" } else { "canonical-parameter" };
        let meta = meta_eval(&source);
        assert!(
            meta.contains("error invalid-form") && meta.contains(reason),
            "meta-eval must reject {name} ({reason}), got: {meta}"
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
