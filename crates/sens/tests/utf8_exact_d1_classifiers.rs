//! #3170 UTF-8 leaf migration: exact D1 controls, original UTF-8 byte laws.
//! Test the library's existing functions; Rust does not redefine any Unicode rule.
use sens::{eval_program, load_core_library, Session};

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core bootstrap");
    eval_program(include_str!("../../../lib/utf8.lisp"), &mut session)
        .expect("current UTF-8 Lisp definitions load");
    session
}

fn bit(session: &mut Session, source: &str) -> bool {
    let outcome = eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"));
    outcome.value.as_predicate_bit()
        .unwrap_or_else(|| panic!("{source}: not an exact D1 predicate: {}", outcome.value))
}

#[test]
fn inclusive_range_and_single_byte_boundaries_return_exact_d1() {
    let mut state = session();
    for (source, expected) in [
        ("(utf8-in-range? 0 0 255)", true),
        ("(utf8-in-range? 255 0 255)", true),
        ("(utf8-in-range? -1 0 255)", false),
        ("(utf8-in-range? 256 0 255)", false),
        ("(utf8-in-range? 42 42 42)", true),
        ("(utf8-in-range? 41 42 42)", false),
        ("(utf8-continuation-byte? 127)", false),
        ("(utf8-continuation-byte? 128)", true),
        ("(utf8-continuation-byte? 191)", true),
        ("(utf8-continuation-byte? 192)", false),
    ] {
        assert_eq!(bit(&mut state, source), expected, "{source}");
    }
}

#[test]
fn three_and_four_byte_second_positions_obey_unicode_exclusions() {
    let mut state = session();
    for (source, expected) in [
        ("(utf8-three-byte-second-ok? 224 159)", false),
        ("(utf8-three-byte-second-ok? 224 160)", true),
        ("(utf8-three-byte-second-ok? 237 159)", true),
        ("(utf8-three-byte-second-ok? 237 160)", false),
        ("(utf8-three-byte-second-ok? 225 128)", true),
        ("(utf8-three-byte-second-ok? 225 127)", false),
        ("(utf8-four-byte-second-ok? 240 143)", false),
        ("(utf8-four-byte-second-ok? 240 144)", true),
        ("(utf8-four-byte-second-ok? 244 143)", true),
        ("(utf8-four-byte-second-ok? 244 144)", false),
        ("(utf8-four-byte-second-ok? 241 128)", true),
        ("(utf8-four-byte-second-ok? 241 192)", false),
    ] {
        assert_eq!(bit(&mut state, source), expected, "{source}");
    }
}

#[test]
fn only_proven_utf8_leaf_helpers_are_migrated_and_others_stay_unchanged() {
    const SOURCE: &str = include_str!("../../../lib/utf8.lisp");
    // This tranche has four independently bounded helpers. A follow-up must
    // prove the legacy integer MOD and b3/b4 continuation mechanism separately.
    for helper in ["utf8-in-range?", "utf8-continuation-byte?",
                   "utf8-three-byte-second-ok?", "utf8-four-byte-second-ok?"] {
        let start = format!("(00001001 {helper}\\n");
        assert_eq!(SOURCE.matches(&start).count(), 1, "{helper} must be defined once");
    }
    assert!(SOURCE.contains("((00011010 value low) (00000010"),
            "inclusive lower bound must classify with exact D1");
}

#[test]
fn old_three_field_cond_is_still_rejected_not_reenabled() {
    let mut state = session();
    let historical = "(00000111 ((00000010 (00000001 ())) (00000001 ()) (00000001 ())))";
    assert!(eval_program(historical, &mut state).is_err(),
            "old expected-value COND must remain fail-closed");
}
