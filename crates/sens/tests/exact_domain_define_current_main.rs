//! Exact-domain DEFINE black-box acceptance for the language-owned mechanism slot.

use sens::{
    eval_parsed_expressions, eval_program, parse, Bit1, Bit2, Bit4, Bit6, Bit7, Bit8, CoreD4,
    CoreD6, CoreD8, DomainIdentity, ErrorKind, Expr, ExprKind, PredicateBit, Racana2, Session,
    SoundD7, Span,
};

fn d1(raw: u8) -> DomainIdentity { PredicateBit::from_word(Bit1::new(raw).unwrap()).into() }
fn d2(raw: u8) -> DomainIdentity { Racana2::from_word(Bit2::new(raw).unwrap()).into() }
fn d4(raw: u8) -> DomainIdentity { CoreD4::from_word(Bit4::new(raw).unwrap()).into() }
fn d6(raw: u8) -> DomainIdentity { CoreD6::from_word(Bit6::new(raw).unwrap()).into() }
fn d7(raw: u8) -> DomainIdentity { SoundD7::from_word(Bit7::new(raw).unwrap()).into() }
fn d8(raw: u8) -> DomainIdentity { CoreD8::from_word(Bit8::new(raw).unwrap()).into() }

fn identity_expr(identity: DomainIdentity) -> Expr {
    Expr { kind: ExprKind::DomainIdentity(identity), span: Span::default() }
}

fn exact_define(target: DomainIdentity, value_source: &str) -> Expr {
    let mut form = parse(&format!("(__define__ __target__ {value_source})"))
        .expect("exact DEFINE witness must parse").remove(0);
    let ExprKind::List(items) = form.kind else { panic!("DEFINE witness must parse as a list"); };
    let mut items = items.to_vec();
    items[0] = identity_expr(d4(0b0011));
    items[1] = identity_expr(target);
    form.kind = ExprKind::List(items.into());
    form
}

fn exact_call(target: DomainIdentity, arguments_source: &str) -> Expr {
    let mut form = parse(&format!("(__call__ {arguments_source})"))
        .expect("exact call witness must parse").remove(0);
    let ExprKind::List(items) = form.kind else { panic!("exact call witness must parse as a list"); };
    let mut items = items.to_vec();
    items[0] = identity_expr(target);
    form.kind = ExprKind::List(items.into());
    form
}

#[test]
fn exact_d6_add1_define_binds_and_invokes_language_owned_closure() {
    let add1 = d6(0b001110);
    let mut session = Session::default();
    eval_parsed_expressions(&[exact_define(add1, "(lambda (x) (+ x 1))")], &mut session)
        .expect("exact D6 ADD1 must bind a language-owned closure");
    let result = eval_parsed_expressions(
        &[exact_call(add1, "7")],
        &mut session,
    ).expect("exact D6 ADD1 invocation");
    assert_eq!(result.value.to_string(), "8");
}

#[test]
fn exact_define_is_single_assignment() {
    let add1 = d6(0b001110);
    let mut session = Session::default();
    eval_parsed_expressions(&[exact_define(add1, "(lambda (x) (+ x 1))")], &mut session).unwrap();
    let error = eval_parsed_expressions(
        &[exact_define(add1, "this-symbol-must-not-be-evaluated")], &mut session,
    ).expect_err("duplicate exact definition must fail before replacement evaluation");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
    assert!(error.message.contains("already has a language-owned binding"));
    assert_eq!(
        eval_parsed_expressions(&[exact_call(add1, "7")], &mut session).unwrap().value.to_string(),
        "8"
    );
}

#[test]
fn noncallable_domains_and_unadmitted_d6_flip_fail_closed() {
    for target in [d1(1), d2(1), d6(0b101101), d7(0b0101101), d8(0b00101101)] {
        let error = eval_parsed_expressions(
            &[exact_define(target, "this-symbol-must-not-be-evaluated")],
            &mut Session::default(),
        ).expect_err("non-callable target must fail closed");
        assert_eq!(error.kind, ErrorKind::InvalidForm);
        assert!(error.message.contains("callable D3/D4/D5/D6"));
    }
}

#[test]
fn exact_define_rejects_plain_data_and_symbol_define_stays_compatible() {
    let error = eval_parsed_expressions(
        &[exact_define(d6(0b001110), "42")], &mut Session::default(),
    ).expect_err("exact callable identity must not accept plain data");
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("callable closure or builtin"));
    let result = eval_program("(def ordinary 7) ordinary", &mut Session::default())
        .expect("symbol DEFINE behavior must remain unchanged");
    assert_eq!(result.value.to_string(), "7");
}
