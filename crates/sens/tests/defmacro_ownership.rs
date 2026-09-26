use sens::{eval_program, parse, Environment, ErrorKind, Session, Value};

#[test]
fn bare_kernel_root_does_not_own_defmacro() {
    let root = Environment::root();
    assert!(root.get("defmacro").is_none());

    let expression = parse("(defmacro id (x) x)")
        .expect("probe should parse")
        .into_iter()
        .next()
        .expect("one expression");
    let error = sens::eval_expr(&expression, &root)
        .expect_err("bare kernel must not implement defmacro");
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn default_session_bootstraps_language_owned_defmacro() {
    let session = Session::default();
    assert!(matches!(
        session.environment.get("defmacro"),
        Some(Value::Macro(_))
    ));
}

#[test]
fn defmacro_executes_through_generic_macro_application() {
    let mut session = Session::default();
    let result = eval_program("(defmacro identity (x) x) (identity 42)", &mut session)
        .expect("language-owned defmacro should define a callable macro");
    assert_eq!(result.value.to_string(), "42");
}

#[test]
fn evaluator_source_has_no_defmacro_dispatch_or_rust_fallback() {
    let evaluator = include_str!("../src/eval/mod.rs");
    let core_forms = include_str!("../src/eval/special_forms/core.rs");
    assert!(!evaluator.contains("Some(\"defmacro\")"));
    assert!(!evaluator.contains("evaluate_defmacro"));
    assert!(!core_forms.contains("fn evaluate_defmacro"));
}
