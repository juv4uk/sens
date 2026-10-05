//! #3381 — exact D5 ZEROP / NUMBERP runtime admission.

use sens::{
    eval_parsed_expressions, parse, Bit5, CoreD5, DomainIdentity, Expr, ExprKind, Session, Span,
};

fn run_exact(bits: u8, args_source: &str) -> Result<String, String> {
    let mut session = Session::default();
    let wrapped = format!("(__d5_pred__ {args_source})");
    let mut parsed = parse(&wrapped).map_err(|e| format!("parse: {e:?}"))?;
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        return Err("wrapper-not-list".into());
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D5(
            CoreD5::from_word(Bit5::new(bits).unwrap()),
        )),
        span: Span { start: 0, end: "__d5_pred__".len() },
    };
    form.kind = ExprKind::List(items.into());

    eval_parsed_expressions(&[form], &mut session)
        .map(|o| o.value.to_string())
        .map_err(|e| format!("{:?}: {}", e.kind, e.message))
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
