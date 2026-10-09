//! #3381 — exact D5 ZEROP / NUMBERP runtime witnesses.
//!
//! Operation selection is exact DomainIdentity only. Human spellings and
//! historical Sens8/Sid8 bytes do not participate in these calls.

use sens::{
    eval_parsed_expressions, load_core_library, parse, Bit4, Bit5, CoreD4, CoreD5,
    DomainIdentity, ErrorKind, Expr, ExprKind, Session, Span, Value,
};

fn run_exact(
    identity: DomainIdentity,
    arguments_source: &str,
) -> Result<Value, sens::LanguageError> {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active Core should load");

    let wrapped = format!("(__d5_predicate__ {arguments_source})");
    let mut parsed = parse(&wrapped).expect("witness payload should parse");
    assert_eq!(parsed.len(), 1);

    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("witness wrapper must parse as one list");
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span {
            start: 0,
            end: "__d5_predicate__".len(),
        },
    };
    form.kind = ExprKind::List(items.into());

    eval_parsed_expressions(&[form], &mut session).map(|outcome| outcome.value)
}

fn d5(bits: u8) -> DomainIdentity {
    DomainIdentity::D5(CoreD5::from_word(
        Bit5::new(bits).expect("five-bit D5 coordinate"),
    ))
}

fn d4(bits: u8) -> DomainIdentity {
    DomainIdentity::D4(CoreD4::from_word(
        Bit4::new(bits).expect("four-bit D4 coordinate"),
    ))
}

fn bit(result: Result<Value, sens::LanguageError>) -> bool {
    result
        .expect("exact D5 predicate call should succeed")
        .as_predicate_bit()
        .expect("D5 predicate result must be exact D1")
}

#[test]
fn exact_d5_numeric_predicates_cross_the_d1_boundary() {
    for source in ["0", "#b0"] {
        assert!(
            bit(run_exact(d5(0b01000), source)),
            "canonical zero must satisfy ZEROP: {source}"
        );
        assert!(
            bit(run_exact(d5(0b01001), source)),
            "ZEROP(x)=1 must entail NUMBERP(x)=1 for {source}"
        );
    }

    for source in ["1", "#b1"] {
        assert!(
            !bit(run_exact(d5(0b01000), source)),
            "nonzero admitted number must not satisfy ZEROP: {source}"
        );
        assert!(
            bit(run_exact(d5(0b01001), source)),
            "nonzero admitted number must satisfy NUMBERP: {source}"
        );
    }
}

// The exact historical tolerance boundary and Rational/host-Number carrier
// cases are pinned inside eval::d5_arithmetic where Values can be constructed
// directly without growing source-literal migration debt.

#[test]
fn numberp_returns_exact_d1_no_for_nonnumeric_values() {
    for source in ["'x", "'()", "'(a b)", r#""text""#] {
        let value = run_exact(d5(0b01001), source)
            .unwrap_or_else(|error| panic!("NUMBERP({source}) failed: {error:?}"));
        assert_eq!(
            value.as_predicate_bit(),
            Some(false),
            "NUMBERP must return exact D1:0 for {source}; value={value}"
        );
    }
}

#[test]
fn zerop_rejects_nonnumeric_input_with_named_type_failure() {
    let error = run_exact(d5(0b01000), "'x")
        .expect_err("ZEROP on nonnumeric value must fail rather than invent NO");
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("D5:01000"));
}

#[test]
fn both_predicates_require_exactly_one_argument() {
    for identity in [d5(0b01000), d5(0b01001)] {
        let zero = run_exact(identity, "").expect_err("zero-arity call must fail");
        assert_eq!(zero.kind, ErrorKind::Arity);

        let two = run_exact(identity, "0 0").expect_err("two-arity call must fail");
        assert_eq!(two.kind, ErrorKind::Arity);
    }
}

#[test]
fn exact_width_firewall_prevents_d4_from_acquiring_d5_predicate_meaning() {
    let d5_zero = run_exact(d5(0b01000), "#b0").expect("D5 ZEROP should execute");
    assert_eq!(d5_zero.as_predicate_bit(), Some(true));

    // Truncating the five-bit payload to D4:1000 selects CAAR, not ZEROP.
    let d4_error = run_exact(d4(0b1000), "#b0")
        .expect_err("D4:1000 must not inherit D5:01000 semantics");
    assert_ne!(d4_error.kind, ErrorKind::Arity);

    let d5_number = run_exact(d5(0b01001), "'x").expect("D5 NUMBERP should execute");
    assert_eq!(d5_number.as_predicate_bit(), Some(false));

    // D4:1001 is CADR, not NUMBERP.
    assert!(
        run_exact(d4(0b1001), "'x").is_err(),
        "D4:1001 must not acquire D5:01001 semantics"
    );
}
