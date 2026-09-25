//! #1414 — Core3 selection is a mechanical session fact only.
//! SENS-owned Core3 contracts remain the authority for meaning and admission.

use my_lisp::{load_core3_library, load_core_library, CoreProfile, Session};

#[test]
fn core3_loader_selects_core3_only_after_the_profile_layer_loads() {
    let mut session = Session::default();
    assert_eq!(session.environment.selected_core_profile(), None);

    load_core3_library(&mut session).expect("Core3 profile must load");

    assert_eq!(
        session.environment.selected_core_profile(),
        Some(CoreProfile::Core3)
    );
}

#[test]
fn lexical_child_shares_selected_core3_signal() {
    let mut session = Session::default();
    load_core3_library(&mut session).expect("Core3 profile must load");

    let child = session.environment.child();

    assert_eq!(child.selected_core_profile(), Some(CoreProfile::Core3));
}

#[test]
fn later_explicit_core4_load_replaces_core3_signal_without_implicit_fallback() {
    let mut session = Session::default();
    load_core3_library(&mut session).expect("Core3 profile must load");
    assert_eq!(
        session.environment.selected_core_profile(),
        Some(CoreProfile::Core3)
    );

    load_core_library(&mut session).expect("explicit Core4 load must succeed");

    assert_eq!(
        session.environment.selected_core_profile(),
        Some(CoreProfile::Core4)
    );
}
