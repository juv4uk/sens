use my_lisp::{eval_program, ErrorKind, Session, Value};

#[test]
fn unknown_semantic_callable_identity_fails_closed() {
    let mut session = Session::default();
    session
        .environment
        .define("mystery-semantic", Value::SemanticRef(255));

    let error = eval_program("(mystery-semantic)", &mut session)
        .expect_err("an unknown semantic callable identity must fail closed");

    assert_eq!(error.kind, ErrorKind::Type);
    assert_eq!(error.message, "unknown semantic callable SID: 11111111");
}
