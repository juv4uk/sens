use sens::{eval_program, load_core_library, Environment, ErrorKind, Session, Value};

#[test]
fn bare_root_stays_smaller_than_macro_bootstrap() {
    let root = Environment::root();
    assert!(root.get("make-macro").is_none());
}

#[test]
fn standard_session_installs_make_macro_as_a_first_class_builtin() {
    let session = Session::default();
    assert!(matches!(
        session.environment.get("make-macro"),
        Some(Value::Builtin(_))
    ));
}

#[test]
fn canonical_core_loader_installs_make_macro_for_a_bare_root_session() {
    let mut session = Session {
        environment: Environment::root(),
    };
    assert!(session.environment.get("make-macro").is_none());

    load_core_library(&mut session).expect("canonical bootstrap should install macro substrate");

    assert!(matches!(
        session.environment.get("make-macro"),
        Some(Value::Builtin(_))
    ));
}

#[test]
fn aliased_make_macro_constructs_a_working_macro_without_head_name_dispatch() {
    let mut session = Session::default();
    let result = eval_program(
        r#"
        (define constructor make-macro)
        (define identity-macro (constructor (lambda (x) x)))
        (identity-macro 42)
        "#,
        &mut session,
    )
    .expect("aliased first-class make-macro should construct a macro");

    assert_eq!(result.value.to_string(), "42");
}

#[test]
fn aliased_make_macro_preserves_named_arity_and_type_failures() {
    let mut session = Session::default();
    eval_program("(define constructor make-macro)", &mut session)
        .expect("make-macro should be bindable as an ordinary value");

    let arity = eval_program("(constructor)", &mut session)
        .expect_err("zero arguments must fail with Arity");
    assert_eq!(arity.kind, ErrorKind::Arity);

    let ty = eval_program("(constructor 42)", &mut session)
        .expect_err("non-closure argument must fail with Type");
    assert_eq!(ty.kind, ErrorKind::Type);
}

#[test]
fn canonical_make_macro_name_obeys_ordinary_lexical_shadowing() {
    let mut session = Session::default();
    let result = eval_program(
        "(define make-macro (lambda (x) (quote shadowed))) (make-macro 42)",
        &mut session,
    )
    .expect("make-macro head position must resolve through the ordinary environment");

    assert_eq!(result.value.to_string(), "shadowed");
}

#[test]
fn evaluator_source_has_no_make_macro_head_dispatch() {
    let evaluator = include_str!("../src/eval/mod.rs");
    assert!(!evaluator.contains("Some(\"make-macro\")"));
    assert!(!evaluator.contains("make-macro expects a closure"));
}
