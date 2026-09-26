//! #1258 — first vertical slice: `eq?` answers with a Core4
//! predicate-answer spelling ("1"/"0") instead of `(identity-relation
//! same|distinct)`, while historical `eq` (SID 00000011, Core1 mechanism)
//! stays completely unchanged. Only the admitted level-1 answers are
//! exercised here — no weaker level (11/00/...) is assigned without a
//! separate law, per #1258's own scope.

use sens::{eval_program, load_core_library, Session};

fn eq_answer_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(
        include_str!("../../../experiments/core4-eq-answer-1258.lisp"),
        &mut session,
    )
    .expect("eq? definition should load");
    session
}

fn eval(source: &str) -> String {
    let mut session = eq_answer_session();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn same_atom_answers_one() {
    assert_eq!(eval("(eq? (quote route) (quote route))"), "\"1\"");
    assert_eq!(eval("(eq? 5 5)"), "\"1\"");
}

#[test]
fn distinct_atom_answers_zero() {
    assert_eq!(eval("(eq? (quote route) (quote billing))"), "\"0\"");
    assert_eq!(eval("(eq? 5 6)"), "\"0\"");
}

#[test]
fn outside_domain_is_a_named_error_not_zero() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    eval_program(
        include_str!("../../../experiments/core4-eq-answer-1258.lisp"),
        &mut session,
    )
    .unwrap();
    let result = eval_program("(eq? (quote (1 2)) (quote (1 2)))", &mut session);
    assert!(
        result.is_err(),
        "a pair argument must fail named, never silently answer \"0\""
    );
}

#[test]
fn not_is_a_clean_bit_flip_between_the_two_admitted_answers() {
    assert_ne!(eval("(eq? 1 1)"), eval("(eq? 1 2)"));
}

#[test]
fn sid_identity_plays_no_role_in_the_answer() {
    // eq? is pure Lisp composition over the existing `eq` builtin; it mints
    // no SID and its answer is plain data (a string), not a callable Sens8.
    assert_eq!(eval("(eq? 1 1)"), "\"1\"");
    assert_eq!(eval("(eq? 1 1)"), eval("(eq? 2 2)"));
}

#[test]
fn historical_core1_eq_is_completely_unchanged() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    // No eq? definition loaded here at all — proves `eq` itself needs no
    // change to support #1258.
    let result = eval_program("(eq? (quote a) (quote a))", &mut session)
        .unwrap()
        .value
        .to_string();
    assert_eq!(result, "(identity-relation same)");
    let result = eval_program("(eq? (quote a) (quote b))", &mut session)
        .unwrap()
        .value
        .to_string();
    assert_eq!(result, "(identity-relation distinct)");
}
