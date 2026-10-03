//! #1272/#2375 — one active Core has no runtime profile selector.
//! Mechanism-lab admission is an orthogonal session fact.

use sens::{load_core_library, Environment, Session};

#[test]
fn bare_root_has_no_mechanism_lab_admission() {
    let environment = Environment::root();
    assert!(!environment.mechanism_lab_enabled());
}

#[test]
fn core_loader_does_not_select_or_enable_a_profile() {
    let mut session = Session::default();
    assert!(!session.environment.mechanism_lab_enabled());

    load_core_library(&mut session).expect("one Core library must load");

    assert!(!session.environment.mechanism_lab_enabled());
}

#[test]
fn lexical_child_shares_the_same_non_lab_session_state() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("one Core library must load");

    let child = session.environment.child();
    assert!(!child.mechanism_lab_enabled());
}
