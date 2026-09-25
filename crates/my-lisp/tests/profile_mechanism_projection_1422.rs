//! #1422 — executable separation of SENS admission from host availability.

use my_lisp::{
    eval_program, load_core3_library, load_core_library, register_sens_capability,
    unregister_sens_capability, Environment, ErrorKind, LanguageError, Sens8, Session, Span, Value,
};
use std::rc::Rc;

const RAW_INVOKE: Sens8 = my_lisp::sens!(10101000);
const UNADMITTED: Sens8 = my_lisp::sens!(11111111);

struct RegistryCleanup;

impl Drop for RegistryCleanup {
    fn drop(&mut self) {
        unregister_sens_capability(RAW_INVOKE);
        unregister_sens_capability(UNADMITTED);
    }
}

fn host_handler(
    sens: Sens8,
    _arguments: &[Value],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    Ok(Value::Symbol(Rc::from(format!("host-executed-{sens}"))))
}

fn error_kind(source: &str, session: &mut Session) -> ErrorKind {
    eval_program(source, session)
        .expect_err("source is expected to fail closed")
        .kind
}

#[test]
fn selected_core_admission_precedes_host_availability() {
    unregister_sens_capability(RAW_INVOKE);
    unregister_sens_capability(UNADMITTED);
    let _cleanup = RegistryCleanup;

    // Availability alone cannot mint admission in an unselected session.
    register_sens_capability(RAW_INVOKE, host_handler);
    let mut unselected = Session::default();
    assert_eq!(
        error_kind("(10101000)", &mut unselected),
        ErrorKind::Type
    );

    // Core4 does not inherit Core3's raw-host admission.
    let mut core4 = Session::default();
    load_core_library(&mut core4).expect("Core4 must load");
    assert_eq!(error_kind("(10101000)", &mut core4), ErrorKind::Type);

    // Core3 admits the route, but admission is not availability.
    unregister_sens_capability(RAW_INVOKE);
    let mut core3 = Session::default();
    load_core3_library(&mut core3).expect("Core3 must load");
    assert_eq!(
        error_kind("(10101000)", &mut core3),
        ErrorKind::MechanismUnavailable
    );

    // Once the separately admitted handler is available, direct SENS and both
    // human surfaces converge on the same exact function/mechanism route.
    register_sens_capability(RAW_INVOKE, host_handler);
    for source in ["(10101000)", "(invoke)", "(викликати)"] {
        let value = eval_program(source, &mut core3)
            .unwrap_or_else(|error| panic!("{source}: {error:?}"))
            .value;
        assert_eq!(value.to_string(), "host-executed-10101000", "{source}");
    }

    // A handler for another existing SENS function does not gain callability
    // because no Core3 admission row exists for it.
    register_sens_capability(UNADMITTED, host_handler);
    assert_eq!(error_kind("(11111111)", &mut core3), ErrorKind::Type);
}
