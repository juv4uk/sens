//! #1272 — runtime carries only which Core profile a loader selected.
//! SENS-owned contracts remain semantic authority for what that profile means.

use sens::{load_core_library, CoreProfile, Environment, Session};

#[test]
fn bare_root_has_no_implicit_core_profile() {
    let environment = Environment::root();
    assert_eq!(environment.selected_core_profile(), None);
}

#[test]
fn core4_loader_selects_core4_explicitly() {
    let mut session = Session::default();
    assert_eq!(session.environment.selected_core_profile(), None);
    load_core_library(&mut session).expect("Core4 library must load");
    assert_eq!(session.environment.selected_core_profile(), Some(CoreProfile::Core4));
}

#[test]
fn lexical_child_shares_the_selected_profile_signal() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 library must load");
    let child = session.environment.child();
    assert_eq!(child.selected_core_profile(), Some(CoreProfile::Core4));
}
