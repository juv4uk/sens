//! #1422 — generated profile-scoped admission gates exact-SENS host availability.

use sens::{
    eval_program, load_core_library, load_mechanism_lab_library, register_sens_capability,
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
fn mechanism_lab_admission_is_required_before_registered_host_execution() {
    let raw = sens::sens!(10101000);
    let unrelated = sens::sens!(11111111);

    unregister_sens_capability(raw);
    unregister_sens_capability(unrelated);
    register_sens_capability(raw, host_handler);

    let mut root = Session::default();
    let root_error = eval_program("(10101000)", &mut root)
        .expect_err("unselected root must not inherit mechanism-lab raw admission");
    assert_eq!(root_error.kind, ErrorKind::Type);

    let mut core = Session::default();
    load_core_library(&mut core).expect("Core loader");
    let core_error = eval_program("(10101000)", &mut core)
        .expect_err("Core4 must not inherit mechanism-lab raw admission");
    assert_eq!(core_error.kind, ErrorKind::Type);

    let mut lab = Session::default();
    load_mechanism_lab_library(&mut lab).expect("mechanism lab loader");
    for source in ["(10101000)", "(invoke)", "(викликати)"] {
        let value = eval_program(source, &mut lab)
            .unwrap_or_else(|error| panic!("{source}: mechanism-lab admitted route should execute: {error:?}"))
            .value;
        assert_eq!(value, Value::Number(42.0, Exactness::Exact), "source: {source}");
    }

    unregister_sens_capability(raw);

    let mut lab_missing = Session::default();
    load_mechanism_lab_library(&mut lab_missing).expect("mechanism lab loader");
    let missing_error = eval_program("(10101000)", &mut lab_missing)
        .expect_err("admitted route without installed handler must fail named");
    assert_eq!(missing_error.kind, ErrorKind::MechanismUnavailable);

    register_sens_capability(unrelated, host_handler);

    let mut lab_unrelated = Session::default();
    load_mechanism_lab_library(&mut lab_unrelated).expect("mechanism lab loader");
    let unrelated_error = eval_program("(11111111)", &mut lab_unrelated)
        .expect_err("host registration cannot mint a mechanism-lab admission row");
    assert_eq!(unrelated_error.kind, ErrorKind::Type);

    unregister_sens_capability(unrelated);
}
