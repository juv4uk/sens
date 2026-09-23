use my_lisp::{eval_program, ErrorKind, Session, Value};

#[test]
fn unknown_sid_identity_fails_closed_when_invoked() {
    let mut session = Session::default();
    session
        .environment
        .define("mystery-semantic", Value::Sid(my_lisp::sid!(11111111)));

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


#[test]
fn early_sid_lowering_resolves_peer_surfaces_before_backend_entry() {
    let mut session = Session::default();
    my_lisp::load_core_library(&mut session).expect("core library must load before Lisp-owned registry API");
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

    let rendered = eval_program(
        "(early-sid-lowering-witness)",
        &mut session,
    )
    .expect("early SID lowering witness must execute")
    .value
    .to_string();

    assert_eq!(rendered, "((same 00000010) yes no (structural-relation same) (structural-relation same) (structural-relation same) (structural-relation same) ())");
}
