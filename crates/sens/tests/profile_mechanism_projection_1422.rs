//! #1422 — generated profile-scoped admission gates exact-SENS host availability.

use sens::{
    eval_program, load_core3_library, load_core_library, register_sens_capability,
    unregister_sens_capability, Environment, ErrorKind, Exactness, LanguageError, Sens8, Session,
    Span, Value,
};

fn host_handler(
    _sens: Sens8,
    _arguments: &[Value],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    Ok(Value::Number(42.0, Exactness::Exact))
}

#[test]
fn core3_profile_admission_is_required_before_registered_host_execution() {
    let raw = sens::sens!(10101000);
    let unrelated = sens::sens!(11111111);

    unregister_sens_capability(raw);
    unregister_sens_capability(unrelated);
    register_sens_capability(raw, host_handler);

    let mut root = Session::default();
    let root_error = eval_program("(10101000)", &mut root)
        .expect_err("unselected root must not inherit Core3 raw admission");
    assert_eq!(root_error.kind, ErrorKind::Type);

    let mut core4 = Session::default();
    load_core_library(&mut core4).expect("Core4 loader");
    let core4_error = eval_program("(10101000)", &mut core4)
        .expect_err("Core4 must not inherit Core3 raw admission");
    assert_eq!(core4_error.kind, ErrorKind::Type);

    let mut core3 = Session::default();
    load_core3_library(&mut core3).expect("Core3 loader");
    for source in ["(10101000)", "(invoke)", "(викликати)"] {
        let value = eval_program(source, &mut core3)
            .unwrap_or_else(|error| panic!("{source}: Core3 admitted route should execute: {error:?}"))
            .value;
        assert_eq!(value, Value::Number(42.0, Exactness::Exact), "source: {source}");
    }

    unregister_sens_capability(raw);

    let mut core3_missing = Session::default();
    load_core3_library(&mut core3_missing).expect("Core3 loader");
    let missing_error = eval_program("(10101000)", &mut core3_missing)
        .expect_err("admitted route without installed handler must fail named");
    assert_eq!(missing_error.kind, ErrorKind::MechanismUnavailable);

    register_sens_capability(unrelated, host_handler);

    let mut core3_unrelated = Session::default();
    load_core3_library(&mut core3_unrelated).expect("Core3 loader");
    let unrelated_error = eval_program("(11111111)", &mut core3_unrelated)
        .expect_err("host registration cannot mint a Core3 admission row");
    assert_eq!(unrelated_error.kind, ErrorKind::Type);

    unregister_sens_capability(unrelated);
}
