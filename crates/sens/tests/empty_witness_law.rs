use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    eval_parsed_expressions, Bija3, Bit1, Bit3, CoreDomainIdentity, DomainIdentity, ErrorKind,
    PredicateBit, Session, Value,
};
use std::rc::Rc;

fn span() -> Span {
    Span { start: 0, end: 0 }
}

fn d1(bit: u8) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D1(PredicateBit::from_word(
            Bit1::new(bit).unwrap(),
        ))),
        span: span(),
    }
}

fn d3_value(bits: u8) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D3(Bija3::from_word(
            Bit3::new(bits).unwrap(),
        ))),
        span: span(),
    }
}

fn empty() -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(Vec::<Expr>::new().into_boxed_slice())),
        span: span(),
    }
}

fn clause(test: Expr, expression: Expr) -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(vec![test, expression].into_boxed_slice())),
        span: span(),
    }
}

fn d3_call(bits: u8, arguments: Vec<Expr>) -> Expr {
    Expr {
        kind: ExprKind::DomainCall(
            CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(bits).unwrap())),
            Rc::from(arguments.into_boxed_slice()),
        ),
        span: span(),
    }
}

fn cond(clauses: Vec<Expr>) -> Expr {
    d3_call(0b011, clauses)
}

fn eval(expr: Expr) -> Result<Value, sens::LanguageError> {
    let mut session = Session::default();
    Ok(eval_parsed_expressions(&[expr], &mut session)?.value)
}

#[test]
fn canonical_d3_cond_selects_only_exact_d1_one() {
    let value = eval(cond(vec![clause(d1(1), d1(0))])).unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}

#[test]
fn canonical_d3_cond_skips_exact_d1_zero() {
    let value = eval(cond(vec![
        clause(d1(0), d1(1)),
        clause(d1(1), d1(0)),
    ]))
    .unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}

#[test]
fn canonical_d3_cond_skips_structural_empty_without_coercing_it_to_zero() {
    let value = eval(cond(vec![
        clause(empty(), d1(1)),
        clause(d1(1), d1(0)),
    ]))
    .unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));

    let no = eval(d1(0)).unwrap();
    let no_witness = eval(empty()).unwrap();
    assert_eq!(no.as_predicate_bit(), Some(false));
    assert_eq!(no_witness.as_predicate_bit(), None);
    assert_ne!(no, no_witness, "D1:0 NO must remain distinct from D3:000 EMPTY");
}

#[test]
fn two_structural_empty_tests_have_control_force_and_exhaust_to_empty() {
    // EMPTY is not D1:0, but it is an admitted no-witness control result:
    // each clause is skipped for its own typed reason, and exhaustion is EMPTY.
    let value = eval(cond(vec![
        clause(empty(), d1(1)),
        clause(empty(), d1(0)),
    ]))
    .unwrap();

    assert!(matches!(value, Value::Nil));
    assert_eq!(value.as_predicate_bit(), None);

    let no = eval(d1(0)).unwrap();
    assert_ne!(value, no, "EMPTY control force must not collapse to D1:0 NO");
}

#[test]
fn canonical_d3_cond_exhaustion_returns_structural_empty() {
    let value = eval(cond(vec![clause(d1(0), d1(1))])).unwrap();
    assert!(matches!(value, Value::Nil));
    assert_eq!(value.as_predicate_bit(), None);
}

#[test]
fn canonical_d3_cond_rejects_any_other_test_value() {
    let error = eval(cond(vec![clause(d3_value(0b001), d1(1))])).unwrap_err();
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn canonical_d3_cond_rejects_three_part_migration_clause() {
    let three_part = Expr {
        kind: ExprKind::List(Rc::from(vec![d1(1), d1(0), d1(1)].into_boxed_slice())),
        span: span(),
    };
    let error = eval(cond(vec![three_part])).unwrap_err();
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn partial_eq_empty_no_witness_feeds_canonical_cond_directly() {
    // Pair input is outside D3:111 EQ's admitted atom domain. Exact-domain EQ
    // therefore returns structural EMPTY/no-witness, which canonical D3:011
    // must skip without conflating it with D1:0.
    let pair = d3_call(0b100, vec![d1(1), d1(0)]);
    let partial_eq = d3_call(0b111, vec![pair, d1(1)]);
    let value = eval(cond(vec![
        clause(partial_eq, d1(1)),
        clause(d1(1), d1(0)),
    ]))
    .unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}

#[test]
fn computed_empty_no_witness_can_feed_canonical_cond() {
    let inner = cond(vec![clause(d1(0), d1(1))]);
    let value = eval(cond(vec![
        clause(inner, d1(1)),
        clause(d1(1), d1(0)),
    ]))
    .unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}
