use my_lisp::{eval_program, ErrorKind, Session, Value};

#[test]
fn unknown_semantic_callable_identity_fails_closed() {
    let mut session = Session::default();
    session
        .environment
        .define("mystery-semantic", Value::SemanticRef(my_lisp::sid!(11111111)));

    let error = eval_program("(mystery-semantic)", &mut session)
        .expect_err("an unknown semantic callable identity must fail closed");

    assert_eq!(error.kind, ErrorKind::Type);
    assert_eq!(error.message, "unknown semantic callable SID: 11111111");
}


#[test]
fn bare_unadmitted_sid_literal_fails_closed_through_existing_call_boundary() {
    let mut session = Session::default();
    let error = eval_program("(11111111)", &mut session)
        .expect_err("an unadmitted bare SID literal must not mint callable meaning");

    assert_eq!(error.kind, ErrorKind::Type);
    assert_eq!(error.message, "unknown semantic callable SID: 11111111");
}
