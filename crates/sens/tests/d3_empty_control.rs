//! #4395 — Contract 11.8 witness for exact PredicateBit-only D3:110 control.
//!
//! Structural EMPTY remains distinct from D1:0, but it is not a predicate
//! answer and therefore cannot control canonical exact-domain COND.

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
fn structural_empty_is_not_an_exact_d3_cond_predicate() {
    let error = run(cond(vec![
        clause(empty(), d1(1)),
        clause(d1(1), d1(0)),
    ]))
    .expect_err("structural EMPTY is not PredicateBit");

    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn explicit_d1_no_continues_and_exhaustion_is_structural_empty() {
    let value = run(cond(vec![clause(d1(0), d1(1))]))
        .expect("D1:0 is the only exact skip control");

    assert!(matches!(value, Value::Nil));
    assert_eq!(value.as_predicate_bit(), None);
}

#[test]
fn non_d1_values_fail_closed_as_cond_tests() {
    for wrong in [number(0.0), number(1.0), empty()] {
        let error = run(cond(vec![clause(wrong, d1(1))]))
            .expect_err("non-D1 control must fail closed");
        assert_eq!(error.kind, ErrorKind::Type);
    }
}

#[test]
fn historical_truthiness_rows_cannot_reenter_current_tier1_authority() {
    let fixtures = include_str!("../../../tests/fixtures/conformance.lisp");
    for marker in [
        "(cond (0 (quote truthy))",
        "(cond (0 (quote zero-is-truthy))",
        "(cond (() (quote first))",
        "(за-умовою (() (як-є wrong))",
    ] {
        let line = fixtures
            .lines()
            .find(|line| line.contains(marker))
            .expect("historical truthiness fixture must remain explicit provenance");
        assert!(line.contains("(tier . 3)"));
        assert!(line.contains("(role . \"historical-compatibility\")"));
        assert!(line.contains("(compatibility . historical-truthiness)"));
        assert!(!line.contains("(role . \"constitutive\")"));
    }
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

#[test]
fn malformed_exact_d3_cond_clause_shape_fails_before_test_evaluation() {
    // A numeric test would fail with Type if evaluated. A malformed clause
    // must fail with InvalidForm instead; no compatibility evaluation occurs.
    for elements in [
        vec![number(1.0)],
        vec![number(1.0), d1(0), d1(1)],
        vec![number(1.0), d1(0), d1(1), d1(0)],
    ] {
        let bad_clause = Expr {
            kind: ExprKind::List(Rc::from(elements.into_boxed_slice())),
            span: span(),
        };
        let error = run(cond(vec![bad_clause]))
            .expect_err("non-two-part clause must fail closed");
        assert_eq!(error.kind, ErrorKind::InvalidForm);
    }
}
