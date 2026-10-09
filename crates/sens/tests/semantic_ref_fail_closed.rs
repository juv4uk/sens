use sens::{eval_program, ErrorKind, Session, Value};

#[test]
fn function_without_admitted_callable_mechanism_fails_closed_when_invoked() {
    let mut session = Session::default();
    session
        .environment
        .define("mystery-semantic", Value::Sid(sens::sens!(11111111)));

    let error = eval_program("(mystery-semantic)", &mut session)
        .expect_err("a function without a callable mechanism must fail closed");

    assert_eq!(error.kind, ErrorKind::Type);
    assert_eq!(error.message, "SENS function has no admitted callable mechanism: 11111111");
}

#[test]
fn bare_sens_function_without_mechanism_fails_closed_through_existing_call_boundary() {
    let mut session = Session::default();
    let error = eval_program("(11111111)", &mut session)
        .expect_err("a bare SENS function without a mechanism must not mint a callable mechanism");

    assert_eq!(error.kind, ErrorKind::Type);
    assert_eq!(error.message, "SENS function has no admitted callable mechanism: 11111111");
}

#[test]
fn early_sid_lowering_resolves_peer_surfaces_before_backend_entry() {
    let mut session = Session::default();
    sens::load_core_library(&mut session)
        .expect("core library must load before Lisp-owned registry API");
    eval_program(
        include_str!("../../../lib/surface/semantic-registry-api.lisp"),
        &mut session,
    )
    .expect("semantic-registry-api.lisp must load");
    eval_program(
        include_str!("../../../tests/fixtures/early-sid-lowering-witness.lisp"),
        &mut session,
    )
    .expect("early SID witness must load");

    let registry_source = include_str!("../../../lib/surface/semantic-registry.lisp");
    let probe = format!(concat!(
        "(10011100 ((reg (semantic-registry-read-source {registry_source:?}))) ",
        "(10011100 ((a (semantic-registry-id-in reg (00000001 atom?))) ",
        "(b (semantic-registry-id-in reg (00000001 атом?))) ",
        "(c (semantic-registry-id-in reg (00000001 aṇu))) ",
        "(d (semantic-registry-id-in reg (00000001 .?)))) ",
        "(00100111 a b c d (00100010 a a) (00100010 a b) ",
        "(00100010 b c) (00100010 c d))))"
    ));
    eprintln!("D1 SID registry DEBUG: {:?}", eval_program(&probe, &mut session)
        .map(|v| v.value.to_string()).map_err(|e| format!("{e}")));

    let program = format!("(early-sid-lowering-witness {registry_source:?})");
    let rendered = eval_program(&program, &mut session)
        .expect("early SID lowering witness must execute")
        .value
        .to_string();

    assert_eq!(
        rendered,
        "((same 00000010) yes no (1) (1) (1) (1) ())"
    );
}
