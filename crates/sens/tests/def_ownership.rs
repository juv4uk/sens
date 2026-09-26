use sens::{eval_program, ErrorKind, Session};

#[test]
fn historical_def_remains_syntax_only_in_the_default_session() {
    let mut session = Session::default();
    assert!(session.environment.get("def").is_none());

    let value_position = eval_program("def", &mut session)
        .expect_err("contract 3.0 keeps def outside the callable/value namespace");
    assert_eq!(value_position.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn historical_def_still_preserves_program_behavior() {
    let mut session = Session::default();
    let result = eval_program("(def answer (+ 20 22)) answer", &mut session)
        .expect("historical syntax-only def must remain compatible");
    assert_eq!(result.value.to_string(), "42");
}

#[test]
fn definition_behavior_is_derivable_without_claiming_the_def_surface() {
    let mut session = Session::default();
    let result = eval_program(
        r#"
        (defmacro def-derived (name value)
          (cons (quote define)
            (cons name
              (cons value (quote ())))))
        (def-derived answer (+ 20 22))
        answer
        "#,
        &mut session,
    )
    .expect("definition behavior should be expressible through DEFINE + macro expansion");

    assert_eq!(result.value.to_string(), "42");
}

#[test]
fn derived_definition_preserves_definition_error_classes() {
    let prelude = r#"
      (defmacro def-derived (name value)
        (cons (quote define)
          (cons name
            (cons value (quote ())))))
    "#;

    let mut arity_session = Session::default();
    eval_program(prelude, &mut arity_session).expect("derivation prelude should load");
    let arity = eval_program("(def-derived answer)", &mut arity_session)
        .expect_err("wrong derived-definition arity must remain named");
    assert_eq!(arity.kind, ErrorKind::Arity);

    let mut derived_session = Session::default();
    eval_program(prelude, &mut derived_session).expect("derivation prelude should load");
    let derived_invalid = eval_program("(def-derived 42 value)", &mut derived_session)
        .expect_err("non-symbol derived definition name must remain invalid");

    let mut canonical_session = Session::default();
    let canonical_invalid = eval_program("(define 42 value)", &mut canonical_session)
        .expect_err("canonical define rejects the same malformed name");

    assert_eq!(derived_invalid.kind, canonical_invalid.kind);
    assert_eq!(derived_invalid.kind, ErrorKind::InvalidForm);
}
