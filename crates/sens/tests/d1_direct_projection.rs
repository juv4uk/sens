//! D1 is a direct one-bit value, not a function and not D3:EMPTY.
//! #d1:0/#d1:1 is only the temporary human-Lisp projection; the
//! canonical SENS reader uses the bare exact W1 words 0 and 1.
use sens::{
    eval_program, eval_parsed_expressions, parse, parse_canonical_binary,
    DomainIdentity, Exactness, ExprKind, Session, Value,
};

#[test]
fn historical_reader_projects_only_two_explicit_d1_words() {
    for (source, exact, expected) in [("#d1:0", "0", false), ("#d1:1", "1", true)] {
        let parsed = parse(source).expect("typed D1 projection");
        assert!(matches!(parsed[0].kind, ExprKind::DomainIdentity(DomainIdentity::D1(_))));
        let direct = eval_program(source, &mut Session::default())
            .expect("direct D1, without evaluating ATOM/NOT").value;
        let canonical_ast = parse_canonical_binary(exact).expect("canonical one-bit source");
        let canonical = eval_parsed_expressions(&canonical_ast, &mut Session::default())
            .expect("canonical D1 evaluation").value;
        assert_eq!(direct.as_predicate_bit(), Some(expected));
        assert_eq!(canonical, direct);
    }
}

#[test]
fn bare_numerals_are_not_reinterpreted_in_historical_source() {
    for source in ["0", "1"] {
        let ast = parse(source).expect("historical number reader");
        assert!(matches!(ast[0].kind, ExprKind::Number(_, Exactness::Exact)));
        let value = eval_program(source, &mut Session::default()).unwrap().value;
        assert_eq!(value.as_predicate_bit(), None);
    }
}

#[test]
fn structural_empty_is_never_boolean_false() {
    let empty = eval_program("(001 ())", &mut Session::default())
        .expect("D3 quote structural empty").value;
    let zero = eval_program("#d1:0", &mut Session::default())
        .expect("direct D1 NO").value;
    assert!(matches!(empty, Value::Nil));
    assert_eq!(empty.as_predicate_bit(), None);
    assert_eq!(zero.as_predicate_bit(), Some(false));
    assert_ne!(empty, zero);
}

#[test]
fn malformed_d1_projections_fail_closed() {
    for source in ["#d1:", "#d1:00", "#d1:01", "#d1:10", "#d1:2",
                   "#d1:-1", "#d1:1x", "#d1:000", "#d1:YES"] {
        assert!(parse(source).is_err(), "must reject {source}");
    }
    // The canonical wire grammar accepts only raw exact-width bits, never
    // this human-readable compatibility sigil.
    assert!(parse_canonical_binary("#d1:1").is_err());
}

#[test]
fn cond_consumes_direct_d1_without_hidden_truthiness() {
    for (condition, expected) in [("#d1:1", "yes"), ("#d1:0", "no")] {
        let source = format!(
            "(110 (({condition} (001 yes))) ((#d1:1 (001 no))))"
        );
        // Extra clause parenthesization would change semantics: construct
        // canonical two-field branches directly.
        let source = format!("(110 ({condition} (001 yes)) (#d1:1 (001 no)))");
        let actual = eval_program(&source, &mut Session::default())
            .expect("exact D1 predicate must control COND").value;
        assert_eq!(actual.to_string(), expected);
    }
}
