//! Canonical reader mechanics for decimal comma aliases (Contract 5.0).
//! Retired three-part COND / legacy Lisp truth assertions are not Rust oracles.
//! Execution and semantic parity of historical fixtures need separate admission.

use sens::{parse, Exactness, ExprKind};

#[test]
fn decimal_comma_reader_preserves_exact_rational_identity() {
    // Both source spellings must parse to the same exact numeric value.
    // Integral scientific values may use a compact Exact Number; fractional
    // values must retain their exact Rational rather than approximate f64.
    for (comma, dot) in [
        ("12,455", "12.455"),
        ("-0,25", "-0.25"),
        ("1,5e3", "1.5e3"),
    ] {
        let left = parse(comma).expect("decimal comma must parse");
        let right = parse(dot).expect("decimal point must parse");
        assert_eq!(left.len(), 1);
        assert_eq!(right.len(), 1);

        match (&left[0].kind, &right[0].kind) {
            (ExprKind::Rational(a), ExprKind::Rational(b)) => {
                assert_eq!(a, b, "{comma} and {dot} must be the same exact rational");
            }
            (ExprKind::Number(a, Exactness::Exact), ExprKind::Number(b, Exactness::Exact)) => {
                assert_eq!(a, b, "{comma} and {dot} must be the same exact integer");
            }
            (a, b) => panic!("both spellings must be identical exact numbers: {a:?} vs {b:?}"),
        }
    }
}

#[test]
fn comma_inside_non_numeric_tokens_remains_symbol_data() {
    for source in ["а,б", "версія1,2", "1,2,3", "1,2.3"] {
        let parsed = parse(source).expect("non-numeric comma token must parse");
        assert_eq!(parsed.len(), 1);
        assert!(
            matches!(&parsed[0].kind, ExprKind::Symbol(_)),
            "{source} must remain a symbol"
        );
    }
}
