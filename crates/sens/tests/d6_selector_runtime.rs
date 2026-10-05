//! #3394 — exact D6 selector runtime admission after Contract 11.5.
//!
//! Residency is not callability: only the proved selector family is admitted
//! by this slice. Other D6 residents, current non-callable D7, and research D8 fail closed.

use sens::{
    eval_parsed_expressions, parse, Bit6, Bit7, Bit8, CoreD6, CoreD8, DomainIdentity, Expr,
    ExprKind, LanguageError, Session, SoundD7, Span,
};

fn run_identity(identity: DomainIdentity, args_source: &str) -> Result<String, LanguageError> {
    let mut session = Session::default();
    let wrapped = format!("(__d6_probe__ {args_source})");
    let mut parsed = parse(&wrapped).expect("probe source");
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("probe wrapper must be a list");
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span {
            start: 0,
            end: "__d6_probe__".len(),
        },
    };
    form.kind = ExprKind::List(items.into());

    eval_parsed_expressions(&[form], &mut session).map(|outcome| outcome.value.to_string())
}

fn d6(raw: u8) -> DomainIdentity {
    CoreD6::from_word(Bit6::new(raw).unwrap()).into()
}

#[test]
fn typed_d6_selector_reaches_the_generator_through_the_real_evaluator() {
    assert_eq!(
        run_identity(d6(0b100000), "'((((a))))").unwrap(),
        "a",
        "D6:100000 CAAAAR must execute by the depth-4 selector generator"
    );
}

#[test]
fn ratified_but_unimplemented_d6_resident_still_fails_closed() {
    let error = run_identity(d6(0b101000), "'(a b c)")
        .expect_err("D6:101000 MAP is ratified identity but has no mechanism in this slice");
    assert!(
        error.message.contains("no admitted") || error.message.contains("not callable"),
        "unexpected fail-closed error: {error:?}"
    );
}

#[test]
fn equal_numeric_payload_in_d7_or_d8_never_inherits_d6_selector_meaning() {
    let d7: DomainIdentity = SoundD7::from_word(Bit7::new(0b0100000).unwrap()).into();
    let d8: DomainIdentity = CoreD8::from_word(Bit8::new(0b00100000).unwrap()).into();

    for identity in [d7, d8] {
        let error = run_identity(identity, "'((((a))))")
            .expect_err("non-callable D7 or research D8 must not enter the D6 selector decoder");
        assert!(
            error.message.contains("not callable") || error.message.contains("no admitted"),
            "unexpected cross-domain firewall error: {error:?}"
        );
    }
}
