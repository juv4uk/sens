//! sens#3809 — derive bounded D3 compiler roles from ratified L1-L5 laws.
//!
//! The SENS program receives exact authority anchors (D2 OPEN and D3 EMPTY)
//! and a representation-only decomposer.  It contains no D3 coordinate->role
//! table.  Rust compiler_execution_role remains differential oracle only.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    compiler_execution_role, domain_identity_shape_mechanism, eval_parsed_expressions,
    eval_program, load_core_library, Bija3, Bit2, Bit3, Bit4, CompilerExecutionRole, CoreD4,
    DomainIdentity, Racana2, Session, Value,
};
use std::rc::Rc;

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const MECHANISM_NAME: &str = "__compiler_domain_shape_mechanism";

fn span() -> Span {
    Span::default()
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

fn d3(raw: u8) -> DomainIdentity {
    DomainIdentity::D3(Bija3::from_word(Bit3::new(raw).expect("D3 word")))
}

fn d2_open() -> DomainIdentity {
    DomainIdentity::D2(Racana2::from_word(Bit2::new(0b10).expect("D2 OPEN authority anchor")))
}

fn d3_empty() -> DomainIdentity {
    d3(0b000)
}

fn role_tag(role: CompilerExecutionRole) -> &'static str {
    match role {
        CompilerExecutionRole::SelectorHead => "selector-head",
        CompilerExecutionRole::SelectorTail => "selector-tail",
        CompilerExecutionRole::PairConstruct => "pair-construct",
    }
}

fn call_role(identity: DomainIdentity) -> Expr {
    list(vec![
        symbol("compiler-role-from-l1-l5"),
        symbol(MECHANISM_NAME),
        domain(identity),
        domain(d2_open()),
        domain(d3_empty()),
    ])
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active core loads");
    session
        .environment
        .define(MECHANISM_NAME, domain_identity_shape_mechanism());
    eval_program(NUCLEUS, &mut session).expect("compiler nucleus loads");
    session
}

#[test]
fn sens_l1_l5_derivation_matches_rust_oracle_for_all_d3_identities() {
    let mut session = session();

    for raw in 0u8..=0b111 {
        let identity = d3(raw);
        let result = eval_parsed_expressions(&[call_role(identity)], &mut session)
            .unwrap_or_else(|error| panic!("D3:{raw:03b} law derivation failed: {error:?}"))
            .value;
        let oracle = compiler_execution_role(
            identity
                .core_operation()
                .expect("D3 identity has Core operation carrier"),
        );

        match oracle {
            Some(role) => assert!(
                matches!(result, Value::Symbol(ref name) if name.as_ref() == role_tag(role)),
                "D3:{raw:03b} SENS law must match differential Rust oracle"
            ),
            None => assert!(
                matches!(result, Value::Nil),
                "D3:{raw:03b} outside bounded compiler roles must fail closed"
            ),
        }
    }
}

#[test]
fn equal_payload_in_d4_does_not_inherit_d3_compiler_role() {
    let mut session = session();
    let d4_same_payload =
        DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0100).expect("D4 exact word")));

    let result = eval_parsed_expressions(&[call_role(d4_same_payload)], &mut session)
        .expect("non-D3 role query remains a normal fail-closed language result")
        .value;

    assert!(matches!(result, Value::Nil));
}

#[test]
fn nucleus_source_has_no_literal_d3_compiler_coordinate_table() {
    for forbidden in ["D3:100", "D3:011", "D3:111", "100=>", "011=>", "111=>"] {
        assert!(
            !NUCLEUS.contains(forbidden),
            "compiler nucleus must derive roles from law inputs, not literal mapping {forbidden}"
        );
    }
}
