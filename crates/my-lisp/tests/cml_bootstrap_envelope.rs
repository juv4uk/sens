use my_lisp::{eval_program, load_core_library, Session};

#[test]
fn lisp_authored_bootstrap_envelope_is_stable_and_fail_closed() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");

    eval_program(
        include_str!("../../../lib/compiler/cml-bootstrap.lisp"),
        &mut session,
    )
    .expect("CML bootstrap frontend should load");

    eval_program(
        include_str!("../../../tests/fixtures/cml-bootstrap-envelope-witness.lisp"),
        &mut session,
    )
    .expect("CML bootstrap witness should load");

    let rendered = eval_program("(cml-bootstrap-envelope-witness)", &mut session)
        .expect("CML bootstrap witness should execute")
        .value
        .to_string();

    assert_eq!(
        rendered,
        "((cml-bootstrap-request/1 (operator +) (operands (1 2))) (cml-bootstrap-rejected/1 unsupported-form-shape (* 1 2)) (cml-bootstrap-rejected/1 unsupported-form-shape (+ 1)) (cml-bootstrap-rejected/1 unsupported-form-shape ()))"
    );
}

#[test]
fn bootstrap_source_does_not_embed_sid_or_machine_authority() {
    let source = include_str!("../../../lib/compiler/cml-bootstrap.lisp");
    assert!(!source.contains("semantic-id"));
    assert!(!source.contains("x86"));
    assert!(!source.contains("opcode"));
    assert!(!source.contains("machine code"));
}
