//! #1406 — RED witness: host registration is availability, not SENS admission.
//!
//! This test intentionally describes the required architecture. On the current
//! post-#1402 main it is expected to fail until generic host registration can no
//! longer mint ordinary callability for a SENS function with no admitted ordinary callable mechanism.

use sens::{
    eval_program, register_sens_capability, unregister_sens_capability, Environment, LanguageError,
    Sens8, Session, Span, Value,
};

struct RegistrationGuard(Sens8);

impl Drop for RegistrationGuard {
    fn drop(&mut self) {
        unregister_sens_capability(self.0);
    }
}

fn host_handler(
    _sens: Sens8,
    _arguments: &[Value],
    _environment: &Environment,
    _span: Span,
) -> Result<Value, LanguageError> {
    Ok(Value::Nil)
}

#[test]
fn host_registration_alone_must_not_make_function_without_admitted_mechanism_callable() {
    let sens = sens::sens!(11111111);
    unregister_sens_capability(sens);

    let mut before = Session::default();
    let before_error = eval_program("(11111111)", &mut before)
        .expect_err("exact SENS function with no admitted ordinary callable mechanism must not be callable before host registration");

    register_sens_capability(sens, host_handler);
    let _cleanup = RegistrationGuard(sens);

    let mut after = Session::default();
    let after_error = eval_program("(11111111)", &mut after)
        .expect_err("host registration is availability only; it must not mint SENS callability");

    assert_eq!(
        after_error.kind, before_error.kind,
        "host availability must not change ordinary SENS admission"
    );
}
