//! #1414/#2375 — the former Core3 selector is an explicit mechanism lab.
//! It does not select a language Core or semantic law.

use sens::{load_core_library, load_mechanism_lab_library, Session};

#[test]
fn mechanism_lab_is_disabled_until_explicitly_loaded() {
    let mut session = Session::default();
    assert!(!session.environment.mechanism_lab_enabled());

    load_mechanism_lab_library(&mut session).expect("mechanism lab must load");

    assert!(session.environment.mechanism_lab_enabled());
}

#[test]
fn lexical_child_shares_mechanism_lab_admission() {
    let mut session = Session::default();
    load_mechanism_lab_library(&mut session).expect("mechanism lab must load");

    let child = session.environment.child();
    assert!(child.mechanism_lab_enabled());
}

#[test]
fn reloading_the_one_core_does_not_turn_the_lab_into_a_core_profile() {
    let mut session = Session::default();
    load_mechanism_lab_library(&mut session).expect("mechanism lab must load");
    assert!(session.environment.mechanism_lab_enabled());

    load_core_library(&mut session).expect("one Core reload must succeed");

    assert!(session.environment.mechanism_lab_enabled());
}
