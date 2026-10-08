//! sens#3809 — derive bounded D3 compiler roles from ratified L1-L5 laws.
//!
//! Structural law input comes from the provenance-bound generated projection
//! merged by #3814.  Host code below only parses/transports that projection
//! into ordinary SENS values.  SENS code performs the role derivation.
//! Rust compiler_execution_role remains differential oracle only.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    compiler_execution_role, domain_identity_shape_mechanism, eval_parsed_expressions,
    load_core_library, parse_mixed_exact_domain, Bija3, Bit3, Bit4, CompilerExecutionRole, CoreD4,
    DomainIdentity, Exactness, Session, Value,
};
use std::rc::Rc;

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const LAW_PROJECTION: &str =
    include_str!("../../../knowledge/bija3-l1-l5-structure-projection.json");
const MECHANISM_NAME: &str = "__compiler_domain_shape_mechanism";
const LAW_NAME: &str = "__compiler_l1_l5_law";

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

fn role_tag(role: CompilerExecutionRole) -> &'static str {
    match role {
        CompilerExecutionRole::SelectorHead => "selector-head",
        CompilerExecutionRole::SelectorTail => "selector-tail",
        CompilerExecutionRole::PairConstruct => "pair-construct",
    }
}

fn quoted_json_string(key: &str) -> String {
    let marker = format!("\"{key}\": \"");
    let start = LAW_PROJECTION
        .find(&marker)
        .unwrap_or_else(|| panic!("missing {key} in generated L1-L5 projection"))
        + marker.len();
    let rest = &LAW_PROJECTION[start..];
    let end = rest.find('"').expect("generated JSON string closes");
    rest[..end].to_string()
}

fn projection_width() -> usize {
    let domain = LAW_PROJECTION
        .find("\"domain\"")
        .expect("generated projection has domain block");
    let rest = &LAW_PROJECTION[domain..];
    let marker = "\"width\": ";
    let start = rest.find(marker).expect("domain width present") + marker.len();
    let digits = rest[start..]
        .chars()
        .take_while(|ch| ch.is_ascii_digit())
        .collect::<String>();
    digits.parse().expect("domain width is numeric")
}

fn projection_spine() -> Vec<String> {
    let marker = "\"L5_spine\": [";
    let start = LAW_PROJECTION.find(marker).expect("L5 spine present") + marker.len();
    let tail = &LAW_PROJECTION[start..];
    let end = tail.find(']').expect("L5 spine closes");
    let block = &tail[..end];

    block
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(|item| item.trim_matches('"').to_string())
        .collect()
}

fn bit_list(bits: &str) -> Value {
    Value::list(bits.bytes().map(|bit| match bit {
        b'0' => Value::predicate_bit(false),
        b'1' => Value::predicate_bit(true),
        other => panic!("non-binary law projection byte: {other}"),
    }))
}

fn law_value() -> Value {
    assert!(
        LAW_PROJECTION.contains("\"status\": \"generated-projection-only\""),
        "compiler law input must remain projection-only"
    );
    assert!(
        LAW_PROJECTION.contains("\"compiler_role_table\": false"),
        "generated law data must not contain a compiler role table"
    );
    for forbidden in ["SelectorHead", "SelectorTail", "PairConstruct"] {
        assert!(
            !LAW_PROJECTION.contains(forbidden),
            "generated structural law data must not precompute role {forbidden}"
        );
    }

    let empty = quoted_json_string("L1_empty");
    let mask = quoted_json_string("L4_dual_xor_mask");
    let spine = projection_spine();

    Value::list([
        Value::Number(projection_width() as f64, Exactness::Exact),
        bit_list(&empty),
        bit_list(&mask),
        Value::list(spine.iter().map(|bits| bit_list(bits))),
    ])
}

fn call_role(identity: DomainIdentity) -> Expr {
    list(vec![
        symbol("compiler-role-from-l1-l5"),
        symbol(MECHANISM_NAME),
        domain(identity),
        symbol(LAW_NAME),
    ])
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active core loads");
    session
        .environment
        .define(MECHANISM_NAME, domain_identity_shape_mechanism());
    session.environment.define(LAW_NAME, law_value());
    let expressions = parse_mixed_exact_domain(NUCLEUS).expect("compiler nucleus parses");
    eval_parsed_expressions(&expressions, &mut session).expect("compiler nucleus loads");
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
