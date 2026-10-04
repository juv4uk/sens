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

fn cond(clauses: Vec<Expr>) -> Expr {
    Expr {
        kind: ExprKind::DomainCall(
            CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b011).unwrap())),
            Rc::from(clauses.into_boxed_slice()),
        ),
        span: span(),
    }
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
    assert_ne!(
        no, no_witness,
        "D1:0 NO must remain distinct from D3:000 EMPTY/no-witness"
    );
}

#[test]
fn canonical_d3_cond_exhaustion_returns_structural_empty() {
    let value = eval(cond(vec![clause(d1(0), d1(1))])).unwrap();
    assert!(matches!(value, Value::Nil));
    assert_eq!(value.as_predicate_bit(), None);
}

#[test]
fn canonical_d3_cond_rejects_any_other_test_value() {
    // D3:001 as data is a domain-qualified semantic object, but not an
    // admitted COND test result.
    let error = eval(cond(vec![clause(d3_value(0b001), d1(1))])).unwrap_err();
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error
        .message
        .contains("D3:011 COND test must return exact D1 PredicateBit"));
}

#[test]
fn canonical_d3_cond_rejects_three_part_migration_clause() {
    let three_part = Expr {
        kind: ExprKind::List(Rc::from(
            vec![d1(1), d1(0), d1(1)].into_boxed_slice(),
        )),
        span: span(),
    };
    let error = eval(cond(vec![three_part])).unwrap_err();
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn computed_empty_no_witness_can_feed_canonical_cond() {
    // Inner canonical COND exhausts to structural EMPTY. The outer canonical
    // COND observes that exact EMPTY/no-witness value, skips it, then selects
    // on exact D1:1. No reader or legacy SID path participates.
    let inner = cond(vec![clause(d1(0), d1(1))]);
    let outer = cond(vec![
        clause(inner, d1(1)),
        clause(d1(1), d1(0)),
    ]);
    let value = eval(outer).unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}
