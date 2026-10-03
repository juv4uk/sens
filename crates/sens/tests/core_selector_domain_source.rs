use sens::{eval_program, Session};

fn session_with_active_core() -> Session {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("active Core must load without rebinding generated D4 selectors");
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

#[test]
fn ratified_d4_selectors_execute_directly_from_exact_source() {
    let mut session = session_with_active_core();

    assert_eq!(eval(&mut session, "(1010 (001 ((7 8) 9)))"), "7"); // CAAR
    assert_eq!(eval(&mut session, "(1011 (001 (7 8 9)))"), "8"); // CADR
    assert_eq!(eval(&mut session, "(1100 (001 ((7 8) 9)))"), "(8)"); // CDAR
    assert_eq!(eval(&mut session, "(1101 (001 (7 8 9)))"), "(9)"); // CDDR
}

#[test]
fn active_core_does_not_redefine_generated_selector_descendants() {
    let core = include_str!("../../../lib/core.lisp");

    for legacy_definition in [
        "(00001001 caar",
        "(00001001 cadr",
        "(00001001 cdar",
        "(00001001 cddr",
    ] {
        assert!(
            !core.contains(legacy_definition),
            "generated selector must not have a second closure definition: {legacy_definition}"
        );
    }
}

#[test]
fn cdar_is_a_real_d4_resident_without_historical_descendant_row() {
    let mut session = session_with_active_core();
    assert_eq!(eval(&mut session, "(1100 (001 ((11 12) 13)))"), "(12)");
}
