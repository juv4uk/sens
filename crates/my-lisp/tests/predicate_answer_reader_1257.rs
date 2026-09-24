//! #1257 research: the reader/printer must keep the exact written form and
//! digit count of a homogeneous 2..7-digit `0`/`1` run (a predicate-answer
//! literal under #1254's graduated-binary hypothesis), without colliding
//! with the reserved 8-bit `Sid` lexical space or with ordinary decimal
//! numbers. No cond/eq/structural-kind semantics are exercised here — that
//! is #1258/#1259's job once #1255 lands the Lisp-owned answer table.

use my_lisp::{eval_program, load_core_library, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn zero_family_round_trips_at_every_width_two_through_seven() {
    for width in 2..=7 {
        let token = "0".repeat(width);
        assert_eq!(eval(&format!("(quote {token})")), token);
    }
}

#[test]
fn one_family_round_trips_at_every_width_two_through_seven() {
    for width in 2..=7 {
        let token = "1".repeat(width);
        assert_eq!(eval(&format!("(quote {token})")), token);
    }
}

#[test]
fn width_one_stays_an_ordinary_number_unchanged() {
    // #1254/#1257 only ask that 2..7-digit runs stop losing their length;
    // single `0`/`1` already serve the existing exact-Q boolean convention
    // (`<`, `=`, `utf8-in-range?`, ...) and must keep behaving as numbers.
    assert_eq!(eval("(+ 0 1)"), "1");
    assert_eq!(eval("(+ 1 1)"), "2");
}

#[test]
fn zero_family_is_not_a_number() {
    for width in 2..=7 {
        let token = "0".repeat(width);
        let source = format!("(+ (quote {token}) 1)");
        assert!(
            eval_program(&source, &mut {
                let mut s = Session::default();
                load_core_library(&mut s).unwrap();
                s
            })
            .is_err(),
            "{token} must not be usable as a number in arithmetic"
        );
    }
}

#[test]
fn one_family_is_not_a_number() {
    for width in 2..=7 {
        let token = "1".repeat(width);
        let source = format!("(+ (quote {token}) 1)");
        assert!(
            eval_program(&source, &mut {
                let mut s = Session::default();
                load_core_library(&mut s).unwrap();
                s
            })
            .is_err(),
            "{token} must not be usable as a number in arithmetic"
        );
    }
}

#[test]
fn zero_family_is_structurally_distinct_from_the_number_zero() {
    assert_eq!(eval("(equal? (quote 00) 0)"), "(structural-relation distinct)");
    assert_eq!(eval("(equal? (quote 000) 0)"), "(structural-relation distinct)");
}

#[test]
fn one_family_is_structurally_distinct_from_the_matching_decimal_number() {
    // `11`/`111` as bare tokens are now predicate-answer literals themselves
    // (that is the whole point of this change), so the decimal magnitude
    // has to be constructed arithmetically to compare against.
    assert_eq!(
        eval("(equal? (quote 11) (+ 10 1))"),
        "(structural-relation distinct)"
    );
    assert_eq!(
        eval("(equal? (quote 111) (+ 110 1))"),
        "(structural-relation distinct)"
    );
}

#[test]
fn different_widths_in_the_same_family_are_structurally_distinct() {
    assert_eq!(
        eval("(equal? (quote 00) (quote 000))"),
        "(structural-relation distinct)"
    );
    assert_eq!(
        eval("(equal? (quote 11) (quote 111))"),
        "(structural-relation distinct)"
    );
}

#[test]
fn same_width_same_family_is_structurally_same() {
    assert_eq!(
        eval("(equal? (quote 000) (quote 000))"),
        "(structural-relation same)"
    );
}

#[test]
fn opposite_family_same_width_is_structurally_distinct() {
    assert_eq!(
        eval("(equal? (quote 000) (quote 111))"),
        "(structural-relation distinct)"
    );
}

#[test]
fn exact_eight_bit_runs_remain_sid_lexical_space_unaffected() {
    assert_eq!(eval("(quote 00000000)"), "00000000");
    assert_eq!(eval("(quote 11111111)"), "11111111");
    // A callable Sid (unlike the ground identity 00000000) still dispatches
    // as a semantic call; a predicate-answer literal never does. This
    // difference is itself evidence the two lexical spaces stayed separate.
    assert_eq!(eval("(00000010 5)"), "(structural-kind atom)");
}

#[test]
fn ordinary_decimal_integers_are_unaffected() {
    assert_eq!(eval("(+ 12 1)"), "13");
    assert_eq!(eval("(+ 100 23)"), "123");
}
