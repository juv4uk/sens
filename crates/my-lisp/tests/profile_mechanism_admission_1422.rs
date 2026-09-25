use my_lisp::{
    eval_program, load_core3_library, load_core_library, register_sens_capability, sens,
    unregister_sens_capability, Environment, ErrorKind, LanguageError, Sens8, Session, Span, Value,
};

fn host_handler(
    _sens: Sens8,
    _arguments: &[Value],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    Ok(Value::Nil)
}

#[test]
fn selected_core_controls_registered_host_mechanism_admission() {
    let raw = sens!(10101000);
    let unrelated = sens!(11111111);

    unregister_sens_capability(raw);
    unregister_sens_capability(unrelated);
    register_sens_capability(raw, host_handler);

    let mut root = Session::default();
    let root_error = eval_program("(10101000)", &mut root)
        .expect_err("unselected root must not admit raw host lookup");
    assert_eq!(root_error.kind, ErrorKind::Type);

    let mut core4 = Session::default();
    load_core_library(&mut core4).expect("Core4 loader");
    let core4_error = eval_program("(10101000)", &mut core4)
        .expect_err("Core4 must not inherit Core3 raw admission");
    assert_eq!(core4_error.kind, ErrorKind::Type);

    unregister_sens_capability(raw);
    let mut core3 = Session::default();
    load_core3_library(&mut core3).expect("Core3 loader");
    let unavailable = eval_program("(10101000)", &mut core3)
        .expect_err("admitted route without handler is mechanism unavailability");
    assert_eq!(unavailable.kind, ErrorKind::MechanismUnavailable);

    register_sens_capability(raw, host_handler);
    let admitted = eval_program("(10101000)", &mut core3)
        .expect("Core3 admission plus host availability may execute");
    assert_eq!(admitted.value, Value::Nil);

    register_sens_capability(unrelated, host_handler);
    let unrelated_error = eval_program("(11111111)", &mut core3)
        .expect_err("registration alone must not admit another SENS function");
    assert_eq!(unrelated_error.kind, ErrorKind::Type);

    unregister_sens_capability(raw);
    unregister_sens_capability(unrelated);
}
