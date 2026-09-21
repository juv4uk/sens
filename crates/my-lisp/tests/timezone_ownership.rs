use my_lisp::{
    eval_program, load_core_library, load_time_library, semantic_registry_export, ErrorKind,
    Session, Value,
};

#[test]
fn timezone_detect_public_binding_is_language_owned_over_raw_declarations() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();

    let timezone_sid =
        semantic_registry_export::semantic_id_for_admitted_surface("timezone-detect")
            .expect("timezone-detect must remain admitted by sr/2");
    assert_eq!(
        session.environment.get("timezone-detect"),
        Some(Value::Sid(timezone_sid)),
        "core exposes semantic identity without installing timezone policy"
    );
    let error = eval_program("(timezone-detect)", &mut session)
        .expect_err("unadmitted SID must fail closed before time library loads");
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(session.environment.get("timezone-detect-raw").is_none());
    assert!(matches!(
        session.environment.get("timezone-declarations-raw"),
        Some(Value::Builtin(_))
    ));

    load_time_library(&mut session).unwrap();

    assert!(matches!(
        session.environment.get("timezone-detect"),
        Some(Value::Closure(_))
    ));
    assert!(session.environment.get("timezone-detect-raw").is_none());
    assert!(matches!(
        session.environment.get("timezone-declarations-raw"),
        Some(Value::Builtin(_))
    ));
}
