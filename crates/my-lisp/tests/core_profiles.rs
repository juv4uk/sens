use my_lisp::{
    load_core_profile, parse, CoreProfile, ErrorKind, Session,
};

#[test]
fn four_core_contract_is_one_lisp_owned_document() {
    let source = include_str!("../../../contracts/core-profile-contract.lisp");
    let forms = parse(source).expect("core-profile-contract.lisp must be readable Lisp data");
    assert_eq!(
        forms.len(),
        1,
        "#1131 core profile contract must remain one self-contained Lisp data document"
    );

    for profile in ["core1", "core2", "core3", "core4"] {
        assert!(
            source.contains(&format!("(identity . {profile})")),
            "#1131 contract must declare {profile}"
        );
    }

    assert!(
        source.contains("(profiles-may-redefine-meaning . forbidden)"),
        "#1131 profiles must never become independent semantic authorities"
    );
    assert!(
        source.contains("(profiles-may-renumber-sids . forbidden)"),
        "#1131 profile selection must preserve Sid8 identity"
    );
}

#[test]
fn profile_identity_is_mechanical_and_has_exactly_four_values() {
    assert_eq!(
        CoreProfile::ALL.map(CoreProfile::number),
        [1, 2, 3, 4],
        "core profile numbers are transport identity, not semantic IDs"
    );
    assert_eq!(CoreProfile::Core1.planned_source_path(), "lib/core1.lisp");
    assert_eq!(CoreProfile::Core2.planned_source_path(), "lib/core2.lisp");
    assert_eq!(CoreProfile::Core3.planned_source_path(), "lib/core3.lisp");
    assert_eq!(CoreProfile::Core4.planned_source_path(), "lib/core4.lisp");
}

#[test]
fn undeclared_profile_implementations_fail_closed() {
    for profile in [CoreProfile::Core1, CoreProfile::Core2, CoreProfile::Core3] {
        let mut session = Session::default();
        let error = load_core_profile(&mut session, profile)
            .expect_err("unimplemented core profiles must never fall back to another core");
        assert_eq!(error.kind, ErrorKind::MechanismUnavailable);
        assert!(
            error.message.contains(profile.planned_source_path()),
            "failure must name the missing Lisp-owned profile source"
        );
    }
}

#[test]
fn migration_default_is_explicitly_core4() {
    let mut session = Session::default();
    load_core_profile(&mut session, CoreProfile::Core4)
        .expect("during #1131 migration the existing core library is the admitted Core4 implementation");
}
