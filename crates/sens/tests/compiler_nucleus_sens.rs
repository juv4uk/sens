//! sens#3803 — executable N0 compiler nucleus.
//!
//! This is intentionally a bootstrap/differential witness, not the final
//! self-host proof.  The authority projection is generated from the one
//! production SENS role projection.  The SENS program performs generic exact
//! DomainIdentity lookup and never contains its own D3 bits->meaning table.
//! sens#3806 tracks moving the projection construction itself into SENS.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    compiler_execution_role, eval_parsed_expressions, load_core_library,
    lower_program, parse_mixed_exact_domain, Bija3, Bit3, CompilerExecutionRole, CoreDomainIdentity,
    DomainIdentity, Session, Value,
};
use std::rc::Rc;

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");

fn span() -> Span {
    Span::default()
}

fn d3_core(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).expect("D3 word")))
}

fn d3_value(raw: u8) -> DomainIdentity {
    DomainIdentity::D3(Bija3::from_word(Bit3::new(raw).expect("D3 word")))
}

fn symbol(name: &str) -> Expr {
    Expr {
        kind: ExprKind::Symbol(name.into()),
        span: span(),
    }
}

fn domain(identity: DomainIdentity) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: span(),
    }
}

fn list(items: Vec<Expr>) -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(items.into_boxed_slice())),
        span: span(),
    }
}

fn quote(expr: Expr) -> Expr {
    Expr {
        kind: ExprKind::DomainCall(
            d3_core(0b001),
            Rc::from(vec![expr].into_boxed_slice()),
        ),
        span: span(),
    }
}

fn role_tag(role: CompilerExecutionRole) -> &'static str {
    match role {
        CompilerExecutionRole::SelectorHead => "selector-head",
        CompilerExecutionRole::SelectorTail => "selector-tail",
        CompilerExecutionRole::PairConstruct => "pair-construct",
    }
}

fn authority_projection() -> Expr {
    let rows = (0u8..=0b111)
        .filter_map(|raw| {
            let role = compiler_execution_role(d3_core(raw))?;
            Some(list(vec![
                domain(d3_value(raw)),
                symbol(role_tag(role)),
                symbol("bootstrap-proof"),
                symbol("bootstrap-provenance"),
            ]))
        })
        .collect();
    list(rows)
}

fn call_nucleus(identity: DomainIdentity) -> Expr {
    list(vec![
        symbol("compiler-nucleus"),
        domain(identity),
        quote(authority_projection()),
    ])
}

fn assert_no_legacy_identity(expr: &Expr) {
    match &expr.kind {
        ExprKind::Sid(sid) => panic!("legacy Sid entered SENS compiler nucleus: {sid}"),
        ExprKind::Call(sid, _) => panic!("legacy Call entered SENS compiler nucleus: {sid}"),
        ExprKind::List(items) => {
            for item in items.iter() {
                assert_no_legacy_identity(item);
            }
        }
        ExprKind::Pair(head, tail) => {
            assert_no_legacy_identity(head);
            assert_no_legacy_identity(tail);
        }
        ExprKind::DomainCall(_, args) => {
            for arg in args.iter() {
                assert_no_legacy_identity(arg);
            }
        }
        ExprKind::Number(_, _)
        | ExprKind::Rational(_)
        | ExprKind::BinaryNumber(_)
        | ExprKind::NumericBuffer(_)
        | ExprKind::DomainIdentity(_)
        | ExprKind::String(_)
        | ExprKind::Symbol(_)
        | ExprKind::Local { .. } => {}
    }
}

fn list_values(value: &Value) -> Option<Vec<&Value>> {
    let mut out = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Nil => return Some(out),
            Value::Pair(head, tail) => {
                out.push(head.as_ref());
                cursor = tail.as_ref();
            }
            _ => return None,
        }
    }
}

#[test]
fn nucleus_source_lowers_without_legacy_sid_or_call_nodes() {
    let parsed = parse_mixed_exact_domain(NUCLEUS).expect("compiler nucleus source parses");
    let lowered = lower_program(&parsed);
    assert!(lowered.len() >= 2, "compiler nucleus contains executable language definitions");
    for expression in &lowered {
        assert_no_legacy_identity(expression);
    }
}


#[test]
fn nucleus_top_level_form_failure_is_localized() {
    let expressions =
        parse_mixed_exact_domain(NUCLEUS).expect("compiler nucleus source parses");
    let mut session = Session::default();
    load_core_library(&mut session).expect("active core loads");

    for (index, expression) in expressions.iter().enumerate() {
        if let Err(error) =
            eval_parsed_expressions(std::slice::from_ref(expression), &mut session)
        {
            panic!(
                "compiler nucleus top-level form {index} failed: {error:?}; expression={expression:?}"
            );
        }
    }
}


#[test]
fn nucleus_looks_up_current_d3_roles_by_exact_identity_and_fails_closed() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active core loads");
    let expressions = parse_mixed_exact_domain(NUCLEUS).expect("compiler nucleus parses");
    eval_parsed_expressions(&expressions, &mut session)
        .expect("SENS compiler nucleus loads");

    for raw in 0u8..=0b111 {
        let expected_role = compiler_execution_role(d3_core(raw));
        let result = eval_parsed_expressions(&[call_nucleus(d3_value(raw))], &mut session)
            .unwrap_or_else(|error| panic!("D3:{raw:03b} nucleus call failed: {error:?}"))
            .value;

        match expected_role {
            None => assert!(
                matches!(result, Value::Nil),
                "D3:{raw:03b} is outside the bounded compiler role projection and must fail closed"
            ),
            Some(role) => {
                let row = list_values(&result).expect("authority hit returns one proper row");
                assert_eq!(row.len(), 4, "normalized authority row stays four fields");
                assert_eq!(row[0], &Value::DomainIdentity(d3_value(raw)));
                assert!(
                    matches!(row[1], Value::Symbol(name) if name.as_ref() == role_tag(role)),
                    "D3:{raw:03b} carries the bootstrap-projected abstract role"
                );
                assert!(
                    matches!(row[2], Value::Symbol(name) if name.as_ref() == "bootstrap-proof")
                );
                assert!(
                    matches!(row[3], Value::Symbol(name) if name.as_ref() == "bootstrap-provenance")
                );
            }
        }
    }
}
