use sens::{eval_program, parse, ErrorKind, Exactness, ExprKind, Session, Value};

fn eval_value(session: &mut Session, source: &str) -> Value {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
}

#[test]
fn exact_function_carries_itself_across_two_language_stages() {
    let mut session = Session::default();
    assert_eq!(
        session.environment.selected_core_profile(),
        None,
        "the witness must not depend on a Core profile loader"
    );

    // Stage A is an exact-SENS identity closure. No function surface spelling
    // participates in the transport: the value entering and leaving the stage
    // is the function 00000101 itself.
    let carried = eval_value(&mut session, "((00001000 (f) f) 00000101)");
    assert_eq!(carried, Value::Sid(sens::sens!(00000101)));

    // Stage B receives the stage-A result as its executable head. If stage A
    // had reconstructed a name/string/number instead of carrying the function
    // value, this application would not reach the exact 00000101 mechanism.
    let result = eval_value(
        &mut session,
        "(((00001000 (f) f) 00000101) (00000001 (alpha beta)))",
    );
    assert_eq!(result, Value::Symbol("alpha".into()));

    assert_eq!(
        session.environment.selected_core_profile(),
        None,
        "executing the carried exact function must not select a Core implicitly"
    );
}

#[test]
fn unsupported_exact_function_is_still_carried_as_the_same_function() {
    let mut session = Session::default();

    let carried = eval_value(&mut session, "((00001000 (f) f) 11111111)");
    assert_eq!(carried, Value::Sid(sens::sens!(11111111)));

    let error = eval_program(
        "(((00001000 (f) f) 11111111))",
        &mut session,
    )
    .expect_err("the exact function must fail only at callable-mechanism admission");

    assert_eq!(error.kind, ErrorKind::Type);
    assert_eq!(
        error.message,
        "SENS function has no admitted callable mechanism: 11111111"
    );
}

#[test]
fn exact_function_failure_is_distinct_from_an_exact_like_non_function_token() {
    let parsed = parse("1111111").expect("seven-bit-looking token is valid decimal source");
    assert_eq!(parsed.len(), 1);
    assert!(matches!(
        parsed[0].kind,
        ExprKind::Number(value, Exactness::Exact) if value == 1_111_111.0
    ));

    let mut session = Session::default();
    let error = eval_program(
        "(((00001000 (f) f) 1111111))",
        &mut session,
    )
    .expect_err("a transported decimal value must not become an exact SENS function");

    assert_eq!(error.kind, ErrorKind::Type);
    assert!(
        error.message.contains("expression is not callable"),
        "unexpected non-function failure: {}",
        error.message
    );
    assert!(
        !error.message.contains("no admitted callable mechanism"),
        "a non-eight-bit token must not enter exact-function mechanism admission"
    );
}
