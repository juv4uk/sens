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
        ("(utf8-byte? 0)", true),
        ("(utf8-byte? 255)", true),
        ("(utf8-byte? 256)", false),
        ("(utf8-byte? -1)", false),
        ("(utf8-continuation-byte? 127)", false),
        ("(utf8-continuation-byte? 128)", true),
        ("(utf8-continuation-byte? 191)", true),
        ("(utf8-continuation-byte? 192)", false),
    ] {
        assert_eq!(bit(&mut state, source), expected, "{source}");
    }
}

#[test]
fn proper_byte_sequences_and_nonlist_tails_preserve_their_class() {
    let mut state = session();
    for (source, expected) in [
        ("(utf8-all-bytes? (00000001 ()))", true),
        ("(utf8-all-bytes? (00000001 (0 127 128 255)))", true),
        ("(utf8-all-bytes? (00000001 (1 2 256)))", false),
        ("(utf8-all-bytes? (00000001 (1 -1)))", false),
        ("(utf8-all-bytes? (00000001 (1 . 2)))", false),
        ("(utf8-all-bytes? (00000001 a))", false),
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
        ("(utf8-two-continuations? 128 191)", true),
        ("(utf8-two-continuations? 127 191)", false),
        ("(utf8-two-continuations? 128 192)", false),
    ] {
        assert_eq!(bit(&mut state, source), expected, "{source}");
    }
}

#[test]
fn locate_leaf_comparison_and_integer_carrier_mismatch() {
    let mut state = session();
    for source in [
        "(00011010 127 128)",
        "(utf8-in-range? 127 128 191)",
        "(utf8-continuation-byte? 127)",
        "(utf8-continuation-byte? 128)",
        "(utf8-two-continuations? 127 191)",
        "(00000010 (00000001 (())))",
        "(00010011 0 1)",
        "(00011100 (00010011 0 1) 0)",
    ] {
        let result = eval_program(source, &mut state);
        eprintln!("UTF8_MIGRATION_DIAG {source} => {result:?}");
    }
}

#[test]
fn old_three_field_cond_is_still_rejected_not_reenabled() {
    let mut state = session();
    let historical = "(00000111 ((00000010 (00000001 ())) (00000001 ()) (00000001 ())))";
    assert!(eval_program(historical, &mut state).is_err(),
            "old expected-value COND must remain fail-closed");
}
