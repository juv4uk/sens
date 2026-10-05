//! #3381 — exact D5 ZEROP / NUMBERP runtime admission.

use sens::{
    eval_parsed_expressions, parse, Bit4, Bit5, CoreD4, CoreD5, DomainIdentity, Expr, ExprKind,
    Session, Span,
};

fn run_identity(identity: DomainIdentity, args_source: &str) -> Result<String, String> {
    let mut session = Session::default();
    let wrapped = format!("(__d5_pred__ {args_source})");
    let mut parsed = parse(&wrapped).map_err(|e| format!("parse: {e:?}"))?;
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        return Err("wrapper-not-list".into());
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span { start: 0, end: "__d5_pred__".len() },
    };
    form.kind = ExprKind::List(items.into());

    eval_parsed_expressions(&[form], &mut session)
        .map(|o| o.value.to_string())
        .map_err(|e| format!("{:?}: {}", e.kind, e.message))
}

fn run_exact(bits: u8, args_source: &str) -> Result<String, String> {
    run_identity(
        DomainIdentity::D5(CoreD5::from_word(Bit5::new(bits).unwrap())),
        args_source,
    )
}

#[test]
fn exact_d5_zerop_and_numberp_return_only_d1() {
    assert_eq!(run_exact(0b01000, "0").unwrap(), "1");
    assert_eq!(run_exact(0b01000, "1").unwrap(), "0");

    // #2720/#3032: historical ZEROP is a tolerance policy over the numeric
    // carrier, not an inexact-float-only shortcut. Exact rationals at the
    // boundary must therefore remain accepted, and the first value beyond it
    // must be rejected without converting through f64.
    assert_eq!(run_exact(0b01000, "3/1000000").unwrap(), "1");
    assert_eq!(run_exact(0b01000, "-3/1000000").unwrap(), "1");
    assert_eq!(run_exact(0b01000, "31/10000000").unwrap(), "0");

    assert_eq!(run_exact(0b01001, "42").unwrap(), "1");
    assert_eq!(run_exact(0b01001, "'x").unwrap(), "0");

    let error = run_exact(0b01000, "'x").expect_err("ZEROP must reject nonnumeric carrier");
    assert!(error.contains("Type"), "{error}");
}


#[test]
fn same_packed_payload_in_d4_does_not_inherit_d5_predicate_meaning() {
    let d4_1000 = DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1000).unwrap()));
    let d4_1001 = DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1001).unwrap()));

    let zerop_collision =
        run_identity(d4_1000, "0").expect_err("D4:1000 must remain its D4 selector law");
    let numberp_collision =
        run_identity(d4_1001, "42").expect_err("D4:1001 must remain its D4 selector law");

    assert!(
        !zerop_collision.is_empty() && !numberp_collision.is_empty(),
        "cross-domain collision controls must fail by D4 law, never execute D5 predicates"
    );
}
