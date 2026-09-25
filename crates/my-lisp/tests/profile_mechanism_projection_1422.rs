//! #1422 — generated profile-scoped admission must gate host availability.

use my_lisp::{
    eval_program, load_core3_library, load_core_library, register_sens_capability,
    unregister_sens_capability, Environment, ErrorKind, LanguageError, Sens8, Session, Span, Value,
};
use std::rc::Rc;

fn host_handler(
    _sens: Sens8,
    _arguments: &[Value],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    Ok(Value::Symbol(Rc::from("host-executed")))
}

#[test]
fn core3_profile_admission_is_required_before_registered_host_execution() {
    let raw = my_lisp::sens!(10101000);
    let unrelated = my_lisp::sens!(11111111);

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
    let core3_value = eval_program("(10101000)", &mut core3)
        .expect("Core3 profile admission plus host availability should execute")
        .value;
    assert_eq!(core3_value, Value::Symbol(Rc::from("host-executed")));

    unregister_sens_capability(raw);

    let mut core3_missing = Session::default();
    load_core3_library(&mut core3_missing).expect("Core3 loader");
    let missing_error = eval_program("(10101000)", &mut core3_missing)
        .expect_err("admitted route without installed handler is mechanism-unavailable");
    assert_eq!(missing_error.kind, ErrorKind::MechanismUnavailable);

    register_sens_capability(unrelated, host_handler);

    let mut core3_unrelated = Session::default();
    load_core3_library(&mut core3_unrelated).expect("Core3 loader");
    let unrelated_error = eval_program("(11111111)", &mut core3_unrelated)
        .expect_err("host registration cannot mint a Core3 admission row");
    assert_eq!(unrelated_error.kind, ErrorKind::Type);

    unregister_sens_capability(unrelated);
}
