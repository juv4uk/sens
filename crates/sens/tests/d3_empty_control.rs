//! #3161 — mechanism witness for strong structural EMPTY on canonical D3:110.
//!
//! Semantic authority lives in #3161/#1663. These tests only prove that the
//! current exact-domain evaluator preserves 0 != () while projecting both to
//! COND's "continue" control action.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    eval_parsed_expressions, Bija3, Bit1, Bit3, CoreDomainIdentity, DomainIdentity, ErrorKind,
    Exactness, PredicateBit, Session, Value,
};
use std::rc::Rc;

fn span() -> Span {
    Span { start: 0, end: 0 }
}

fn d1(bit: u8) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D1(PredicateBit::from_word(
            Bit1::new(bit).expect("D1 bit"),
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

fn number(value: f64) -> Expr {
    Expr {
        kind: ExprKind::Number(value, Exactness::Exact),
        span: span(),
    }
}

fn clause(test: Expr, result: Expr) -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(vec![test, result].into_boxed_slice())),
        span: span(),
    }
}

fn cond(clauses: Vec<Expr>) -> Expr {
    Expr {
        kind: ExprKind::DomainCall(
            CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b110).expect("D3:110"))),
            Rc::from(clauses.into_boxed_slice()),
        ),
        span: span(),
    }
}

fn eq(left: Expr, right: Expr) -> Expr {
    Expr {
        kind: ExprKind::DomainCall(
            CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b101).expect("D3:101"))),
            Rc::from(vec![left, right].into_boxed_slice()),
        ),
        span: span(),
    }
}

fn run(expr: Expr) -> Result<Value, sens::LanguageError> {
    let mut session = Session::default();
    eval_parsed_expressions(&[expr], &mut session).map(|result| result.value)
}

#[test]
fn d1_no_and_empty_stay_distinct_values() {
    let no = run(d1(0)).expect("D1:0 evaluates");
    let nil = run(empty()).expect("EMPTY evaluates");

    assert_eq!(no.as_predicate_bit(), Some(false));
    assert_eq!(nil.as_predicate_bit(), None);
    assert!(matches!(nil, Value::Nil));
    assert_ne!(no, nil);
}

#[test]
fn empty_has_control_force_without_becoming_false() {
    let value = run(cond(vec![
        clause(empty(), d1(1)),
        clause(d1(1), d1(0)),
    ]))
    .expect("EMPTY is an admitted no-witness COND input");

    assert_eq!(value.as_predicate_bit(), Some(false));
}

#[test]
fn explicit_no_and_empty_both_continue_but_exhaustion_is_empty() {
    let value = run(cond(vec![
        clause(d1(0), d1(1)),
        clause(empty(), d1(1)),
    ]))
    .expect("D1:0 and EMPTY both project to continue");

    assert!(matches!(value, Value::Nil));
    assert_eq!(value.as_predicate_bit(), None);
}

#[test]
fn only_exact_d1_or_empty_are_admitted_as_cond_tests() {
    let error = run(cond(vec![clause(number(1.0), d1(1))]))
        .expect_err("Number 1 is not PredicateBit 1");

    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn exact_eq_empty_witness_feeds_cond_without_becoming_false() {
    let pair = Expr {
        kind: ExprKind::List(Rc::from(vec![number(1.0)].into_boxed_slice())),
        span: span(),
    };

    let direct = run(eq(pair.clone(), number(1.0)))
        .expect("partial D3 EQ returns EMPTY/no-witness");
    assert!(matches!(direct, Value::Nil));
    assert_eq!(direct.as_predicate_bit(), None);

    let projected = run(cond(vec![
        clause(eq(pair, number(1.0)), d1(1)),
        clause(d1(1), d1(0)),
    ]))
    .expect("COND admits EQ EMPTY as no-witness and continues");

    assert_eq!(projected.as_predicate_bit(), Some(false));
}

#[test]
fn three_part_clause_is_rejected_on_exact_d3_cond() {
    let bad_clause = Expr {
        kind: ExprKind::List(Rc::from(
            vec![d1(1), d1(0), d1(1)].into_boxed_slice(),
        )),
        span: span(),
    };
    let error = run(cond(vec![bad_clause])).expect_err("D3:110 is two-part only");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}
