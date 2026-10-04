//! #3161 / #1708 — exact-domain EMPTY control mechanism witness.
//!
//! Semantic cases and expected outcomes are owned by the Lisp data fixture.
//! Rust only decodes descriptors into exact-domain AST, executes the mechanism,
//! and observes typed results/errors.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    eval_parsed_expressions, parse, Bija3, Bit1, Bit3, CoreDomainIdentity, DomainIdentity,
    ErrorKind, PredicateBit, Session, Value,
};
use std::rc::Rc;

fn span() -> Span {
    Span { start: 0, end: 0 }
}

fn list_items(expr: &Expr) -> &[Expr] {
    match &expr.kind {
        ExprKind::List(items) => items,
        other => panic!("expected descriptor list, got {other:?}"),
    }
}

fn symbol(expr: &Expr) -> &str {
    match &expr.kind {
        ExprKind::Symbol(value) => value.as_ref(),
        other => panic!("expected descriptor symbol, got {other:?}"),
    }
}

fn string(expr: &Expr) -> &str {
    match &expr.kind {
        ExprKind::String(value) => value.as_ref(),
        other => panic!("expected descriptor string, got {other:?}"),
    }
}

fn alist_value<'a>(entries: &'a [Expr], key: &str) -> Option<&'a Expr> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        if matches!(&k.kind, ExprKind::Symbol(name) if &**name == key) {
            Some(v.as_ref())
        } else {
            None
        }
    })
}

fn alist_string<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    alist_value(entries, key).map(string)
}

fn bits3(text: &str) -> u8 {
    assert_eq!(text.len(), 3, "D3 descriptor must have exactly three bits");
    u8::from_str_radix(text, 2).expect("D3 descriptor must contain only 0/1")
}

fn d1(bit: u8) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D1(PredicateBit::from_word(
            Bit1::new(bit).expect("D1 descriptor must be 0/1"),
        ))),
        span: span(),
    }
}

fn d3_value(bits: u8) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D3(Bija3::from_word(
            Bit3::new(bits).expect("D3 descriptor must fit three bits"),
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

fn d3_call(bits: u8, arguments: Vec<Expr>) -> Expr {
    Expr {
        kind: ExprKind::DomainCall(
            CoreDomainIdentity::D3(Bija3::from_word(
                Bit3::new(bits).expect("D3 call descriptor must fit three bits"),
            )),
            Rc::from(arguments.into_boxed_slice()),
        ),
        span: span(),
    }
}

fn descriptor_expr(descriptor: &Expr) -> Expr {
    match &descriptor.kind {
        ExprKind::Symbol(name) if &**name == "empty" => empty(),
        ExprKind::List(items) => {
            assert!(!items.is_empty(), "descriptor list must have a head");
            match symbol(&items[0]) {
                "d1" => {
                    assert_eq!(items.len(), 2, "d1 descriptor arity");
                    d1(string(&items[1]).parse::<u8>().expect("D1 bit must be 0/1"))
                }
                "d3-value" => {
                    assert_eq!(items.len(), 2, "d3-value descriptor arity");
                    d3_value(bits3(string(&items[1])))
                }
                "number" => {
                    assert_eq!(items.len(), 2, "number descriptor arity");
                    Expr {
                        kind: ExprKind::Number(
                            string(&items[1]).parse::<f64>().expect("number descriptor"),
                            sens::Exactness::Exact,
                        ),
                        span: span(),
                    }
                }
                "symbol" => {
                    assert_eq!(items.len(), 2, "symbol descriptor arity");
                    Expr {
                        kind: ExprKind::Symbol(Rc::from(string(&items[1]))),
                        span: span(),
                    }
                }
                "call-d3" => {
                    assert!(items.len() >= 2, "call-d3 descriptor arity");
                    let bits = bits3(string(&items[1]));
                    let args = items[2..].iter().map(descriptor_expr).collect();
                    d3_call(bits, args)
                }
                "cond" => {
                    let clauses = items[1..]
                        .iter()
                        .map(|clause_desc| {
                            let parts = list_items(clause_desc);
                            assert!(
                                !parts.is_empty() && symbol(&parts[0]) == "clause",
                                "COND descriptor entries must be clause forms"
                            );
                            Expr {
                                kind: ExprKind::List(Rc::from(
                                    parts[1..]
                                        .iter()
                                        .map(descriptor_expr)
                                        .collect::<Vec<_>>()
                                        .into_boxed_slice(),
                                )),
                                span: span(),
                            }
                        })
                        .collect();
                    d3_call(0b011, clauses)
                }
                other => panic!("unknown exact-domain descriptor {other:?}"),
            }
        }
        other => panic!("unsupported exact-domain descriptor {other:?}"),
    }
}

fn assert_expected_value(case: &str, descriptor: &Expr, actual: &Value) {
    match &descriptor.kind {
        ExprKind::Symbol(name) if &**name == "empty" => {
            assert!(
                matches!(actual, Value::Nil),
                "{case}: expected structural EMPTY, got {actual}"
            );
            assert_eq!(
                actual.as_predicate_bit(),
                None,
                "{case}: structural EMPTY must not observe as D1"
            );
        }
        ExprKind::List(items) if !items.is_empty() && symbol(&items[0]) == "d1" => {
            assert_eq!(items.len(), 2, "{case}: expected D1 descriptor arity");
            let bit = match string(&items[1]) {
                "0" => false,
                "1" => true,
                other => panic!("{case}: expected D1 bit must be 0/1, got {other:?}"),
            };
            assert_eq!(
                actual.as_predicate_bit(),
                Some(bit),
                "{case}: exact D1 observation mismatch; actual={actual}"
            );
        }
        other => panic!("{case}: unsupported expected value descriptor {other:?}"),
    }
}

fn expected_error_kind(name: &str) -> ErrorKind {
    match name {
        "Type" => ErrorKind::Type,
        "InvalidForm" => ErrorKind::InvalidForm,
        other => panic!("unsupported expected error kind {other:?}"),
    }
}

#[test]
fn lisp_owned_cases_drive_exact_d1_empty_control_mechanism() {
    let source = include_str!("../../../tests/fixtures/empty-witness-law-cases.lisp");
    let forms = parse(source).expect("EMPTY witness fixture must parse as Lisp data");
    assert_eq!(forms.len(), 1, "EMPTY witness fixture must be one data form");

    let rows = list_items(&forms[0]);
    assert!(
        rows.len() >= 10,
        "fixture must retain positive, negative, EMPTY, and partial-EQ coverage"
    );

    for row in rows {
        let entries = list_items(row);
        let case = alist_string(entries, "case").expect("row requires case");
        let program =
            descriptor_expr(alist_value(entries, "program").expect("row requires program"));
        let expected_value = alist_value(entries, "expect-value");
        let expected_error = alist_string(entries, "expect-error");
        assert!(
            expected_value.is_some() ^ expected_error.is_some(),
            "{case}: row must own exactly one expected outcome"
        );

        let mut session = Session::default();
        match eval_parsed_expressions(&[program], &mut session) {
            Ok(result) => {
                assert!(
                    expected_error.is_none(),
                    "{case}: expected error {:?}, got value {}",
                    expected_error,
                    result.value
                );
                assert_expected_value(case, expected_value.expect("expected value"), &result.value);
            }
            Err(error) => {
                let expected = expected_error
                    .unwrap_or_else(|| panic!("{case}: expected value but got error {error}"));
                assert_eq!(
                    error.kind,
                    expected_error_kind(expected),
                    "{case}: error kind mismatch: {error}"
                );
            }
        }
    }
}
