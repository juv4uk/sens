//! #3655 — exact-domain DEFINE installs language-owned mechanisms without surfaces.

use sens::{
    eval_parsed_expressions, eval_program, parse, Bit1, Bit2, Bit4, Bit6, Bit7, Bit8, CoreD4,
    CoreD6, CoreD8, DomainIdentity, ErrorKind, Expr, ExprKind, PredicateBit, Racana2, Session,
    SoundD7, Span,
};

fn d1(raw: u8) -> DomainIdentity {
    PredicateBit::from_word(Bit1::new(raw).unwrap()).into()
}

fn d2(raw: u8) -> DomainIdentity {
    Racana2::from_word(Bit2::new(raw).unwrap()).into()
}

fn d4(raw: u8) -> DomainIdentity {
    CoreD4::from_word(Bit4::new(raw).unwrap()).into()
}

fn d6(raw: u8) -> DomainIdentity {
    CoreD6::from_word(Bit6::new(raw).unwrap()).into()
}

fn d7(raw: u8) -> DomainIdentity {
    SoundD7::from_word(Bit7::new(raw).unwrap()).into()
}

fn d8(raw: u8) -> DomainIdentity {
    CoreD8::from_word(Bit8::new(raw).unwrap()).into()
}

fn identity_expr(identity: DomainIdentity) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span::default(),
    }
}

fn exact_define(target: DomainIdentity, value_source: &str) -> Expr {
    let wrapped = format!("(__define__ __target__ {value_source})");
    let mut parsed = parse(&wrapped).expect("exact DEFINE witness must parse");
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("DEFINE witness must parse as a list");
    };
    let mut items = items.to_vec();
    items[0] = identity_expr(d4(0b0011)); // current D4 DEFINE
    items[1] = identity_expr(target);
    form.kind = ExprKind::List(items.into());
    form
}

fn exact_call(target: DomainIdentity, arguments_source: &str) -> Expr {
    let wrapped = format!("(__call__ {arguments_source})");
    let mut parsed = parse(&wrapped).expect("exact call witness must parse");
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("exact call witness must parse as a list");
    };
    let mut items = items.to_vec();
    items[0] = identity_expr(target);
    form.kind = ExprKind::List(items.into());
    form
}

#[test]
fn exact_d6_define_binds_and_invokes_a_language_owned_flip_closure() {
    // Current D6 authority: 101101 = FLIP.
    let flip = d6(0b101101);
    let mut session = Session::default();

    let definition = exact_define(flip, "(lambda (f a b) (f b a))");
    eval_parsed_expressions(&[definition], &mut session)
        .expect("exact D6 FLIP target should accept a language-owned closure");

    let call = exact_call(
        flip,
        "(lambda (x y) (cons x (cons y (quote ())))) 7 2",
    );
    let result = eval_parsed_expressions(&[call], &mut session)
        .expect("exact D6 FLIP target should invoke through domain_code_slot");

    assert_eq!(result.value.to_string(), "(2 7)");
}

#[test]
fn exact_define_is_single_assignment_and_rejects_before_replacement_evaluation() {
    let flip = d6(0b101101);
    let mut session = Session::default();

    eval_parsed_expressions(
        &[exact_define(flip, "(lambda (f a b) (f b a))")],
        &mut session,
    )
    .expect("first exact definition must bind");

    let error = eval_parsed_expressions(
        &[exact_define(flip, "this-symbol-must-not-be-evaluated")],
        &mut session,
    )
    .expect_err("second exact definition must fail before evaluating replacement");

    assert_eq!(error.kind, ErrorKind::InvalidForm);
    assert!(
        error.message.contains("already has a language-owned binding"),
        "unexpected duplicate-definition error: {error:?}"
    );
}

#[test]
fn non_callable_d1_d2_d7_and_d8_targets_fail_closed_before_value_evaluation() {
    for target in [d1(1), d2(1), d7(0b0101101), d8(0b00101101)] {
        let error = eval_parsed_expressions(
            &[exact_define(target, "this-symbol-must-not-be-evaluated")],
            &mut Session::default(),
        )
        .expect_err("D1/D2/D7/D8 must not become callable DEFINE targets by width");

        assert_eq!(error.kind, ErrorKind::InvalidForm);
        assert!(
            error.message.contains("callable D3/D4/D5/D6"),
            "unexpected non-callable target error: {error:?}"
        );
    }
}

#[test]
fn exact_define_rejects_non_callable_values() {
    let error = eval_parsed_expressions(
        &[exact_define(d6(0b101101), "42")],
        &mut Session::default(),
    )
    .expect_err("exact callable identity must not accept plain data");

    assert_eq!(error.kind, ErrorKind::Type);
    assert!(
        error.message.contains("callable closure or builtin"),
        "unexpected exact-value error: {error:?}"
    );
}

#[test]
fn symbol_define_behavior_is_unchanged() {
    let result = eval_program("(def ordinary 7) ordinary", &mut Session::default())
        .expect("legacy/source Symbol DEFINE must remain unchanged");
    assert_eq!(result.value.to_string(), "7");
}
