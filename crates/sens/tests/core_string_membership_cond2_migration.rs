//! #2320 — migrate only string-membership-helper from retired ATOM result
//! matching to strict D1 control while preserving the string classifier.
use sens::{eval_program, load_core_library, Session};

fn evaluate(source: &str) -> Result<String, String> {
    let mut session = Session::default();
    load_core_library(&mut session).map_err(|err| format!("load-core: {err:?}"))?;
    eval_program(source, &mut session)
        .map(|out| out.value.to_string())
        .map_err(|err| format!("{:?}: {}", err.kind, err.message))
}

#[test]
fn helper_recognizes_empty_and_nonempty_string_atoms() {
    let member = evaluate("(00000001 (class-membership string member))").unwrap();
    for source in [
        "(string-membership-helper \"\")",
        "(string-membership-helper \"hello\")",
    ] {
        assert_eq!(
            evaluate(source).unwrap_or_else(|err| panic!("{source}: {err}")),
            member,
            "{source} must preserve the serialized leading-quote witness",
        );
    }
}

#[test]
fn helper_preserves_empty_number_symbol_and_pair_nonmembership() {
    let nonmember = evaluate("(00000001 (class-membership string nonmember))").unwrap();
    for source in [
        "(string-membership-helper (00000001 ()))",
        "(string-membership-helper 17)",
        "(string-membership-helper (00000001 hello))",
        "(string-membership-helper (00000001 (a b)))",
        "(string-membership-helper (00000001 (a . b)))",
    ] {
        assert_eq!(
            evaluate(source).unwrap_or_else(|err| panic!("{source}: {err}")),
            nonmember,
            "{source} must stay outside the string atom class",
        );
    }
}

#[test]
fn string_membership_core_mirror_has_single_exact_d1_law() {
    const CORE: &str = include_str!("../../../lib/core.lisp");
    const CORE4: &str = include_str!("../../../lib/core4.lisp");
    const START: &str = "(00001001 string-membership-helper\n";
    for (name, source) in [("core", CORE), ("core4", CORE4)] {
        assert_eq!(source.matches(START).count(), 1, "{name}: duplicate helper");
        let helper = source.split_once(START).unwrap().1
            .split_once("\n(00001001").unwrap().0;
        assert!(helper.contains("((00000011 value (00000001 ()))"),
                "{name}: check empty by exact D3 EQ under ATOM gate");
        assert!(helper.contains("((00000010 (00000001 ()))"),
                "{name}: total D1 fallback required");
        assert!(!helper.contains("((00000010 value) ()"),
                "{name}: obsolete three-field ATOM branch");
    }
}
