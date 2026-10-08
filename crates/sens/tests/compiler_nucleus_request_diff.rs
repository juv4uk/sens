//! sens#3804 — host/reference vs SENS-written compiler nucleus request differential.
//!
//! Semantic coordinates are never copied here. Selector cases come from the one
//! SENS-owned compiler corpus and role meaning comes from the existing Rust
//! differential oracle vs the production SENS nucleus. Proof/provenance fields
//! are transport metadata from the provenance-bound generated L1-L5 projection.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    compiler_execution_role, domain_identity_shape_mechanism, eval_parsed_expressions,
    load_core_library, parse_mixed_exact_domain, sha256_source, Bija3, Bit3, Bit4, Bit8,
    CompilerExecutionRole, CoreD4, CoreD8, DomainIdentity, Exactness,
    Session, Value,
};
use std::rc::Rc;

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const LAW: &str = include_str!("../../../knowledge/bija3-l1-l5-structure-projection.json");
const CORPUS: &str = include_str!("../../../contracts/compiler-d3-selector-corpus-v1.tsv");
const MECHANISM_NAME: &str = "__compiler_domain_shape_mechanism";
const LAW_NAME: &str = "__compiler_l1_l5_law";
const PROOF_NAME: &str = "__compiler_l1_l5_proof";
const PROVENANCE_NAME: &str = "__compiler_l1_l5_provenance";

#[derive(Debug, Clone, PartialEq, Eq)]
struct NormalizedRequest {
    identity: DomainIdentity,
    role: String,
    proof_ref: String,
    provenance: Vec<String>,
}

#[derive(Debug)]
struct LawProjection {
    width: u8,
    l1_empty: String,
    l4_mask: String,
    l5_spine: Vec<String>,
    owner_ratification: String,
    authority_sha256: String,
    projection_sha256: String,
}

fn quoted_field(text: &str, key: &str) -> String {
    let marker = format!("\"{key}\": \"");
    let start = text
        .find(&marker)
        .unwrap_or_else(|| panic!("missing JSON field {key}"))
        + marker.len();
    let rest = &text[start..];
    let end = rest.find('"').expect("JSON string closes");
    rest[..end].to_string()
}

fn integer_field(text: &str, key: &str) -> u8 {
    let marker = format!("\"{key}\": ");
    let start = text
        .find(&marker)
        .unwrap_or_else(|| panic!("missing JSON integer field {key}"))
        + marker.len();
    text[start..]
        .chars()
        .take_while(|ch| ch.is_ascii_digit())
        .collect::<String>()
        .parse()
        .unwrap_or_else(|error| panic!("invalid {key}: {error}"))
}

fn l5_spine(text: &str) -> Vec<String> {
    let marker = "\"L5_spine\": [";
    let start = text.find(marker).expect("L5 spine present") + marker.len();
    let tail = &text[start..];
    let end = tail.find(']').expect("L5 spine closes");
    tail[..end]
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(|item| item.trim_matches('"').to_string())
        .collect()
}

fn law_projection() -> LawProjection {
    LawProjection {
        width: integer_field(LAW, "width"),
        l1_empty: quoted_field(LAW, "L1_empty"),
        l4_mask: quoted_field(LAW, "L4_dual_xor_mask"),
        l5_spine: l5_spine(LAW),
        owner_ratification: quoted_field(LAW, "owner_ratification"),
        authority_sha256: quoted_field(LAW, "sha256"),
        projection_sha256: quoted_field(LAW, "projection_sha256"),
    }
}

fn bit_list(bits: &str) -> Value {
    Value::list(bits.bytes().map(|bit| match bit {
        b'0' => Value::predicate_bit(false),
        b'1' => Value::predicate_bit(true),
        other => panic!("non-binary law byte: {other}"),
    }))
}

fn law_value(law: &LawProjection) -> Value {
    assert!(LAW.contains("\"status\": \"generated-projection-only\""));
    assert!(LAW.contains("\"compiler_role_table\": false"));
    Value::list([
        Value::Number(law.width as f64, Exactness::Exact),
        bit_list(&law.l1_empty),
        bit_list(&law.l4_mask),
        Value::list(law.l5_spine.iter().map(|bits| bit_list(bits))),
    ])
}

fn sha256_hex(bytes: &[u8]) -> String {
    sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn provenance(law: &LawProjection) -> Vec<String> {
    vec![
        law.authority_sha256.clone(),
        law.projection_sha256.clone(),
        sha256_hex(NUCLEUS.as_bytes()),
    ]
}

fn provenance_value(law: &LawProjection) -> Value {
    Value::list(
        provenance(law)
            .into_iter()
            .map(|value| Value::String(Rc::from(value))),
    )
}

fn symbol(name: &str) -> Expr {
    Expr {
        kind: ExprKind::Symbol(name.into()),
        span: Span::default(),
    }
}

fn domain(identity: DomainIdentity) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span::default(),
    }
}

fn list(items: Vec<Expr>) -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(items.into_boxed_slice())),
        span: Span::default(),
    }
}

fn request(identity: DomainIdentity) -> Expr {
    list(vec![
        symbol("compiler-request-from-l1-l5"),
        symbol(MECHANISM_NAME),
        domain(identity),
        symbol(LAW_NAME),
        symbol(PROOF_NAME),
        symbol(PROVENANCE_NAME),
    ])
}

fn session(law: &LawProjection) -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active core loads");
    session
        .environment
        .define(MECHANISM_NAME, domain_identity_shape_mechanism());
    session.environment.define(LAW_NAME, law_value(law));
    session.environment.define(
        PROOF_NAME,
        Value::String(Rc::from(law.owner_ratification.as_str())),
    );
    session
        .environment
        .define(PROVENANCE_NAME, provenance_value(law));
    let expressions = parse_mixed_exact_domain(NUCLEUS).expect("compiler nucleus parses");
    eval_parsed_expressions(&expressions, &mut session).expect("compiler nucleus loads");
    session
}

fn list_values(value: &Value) -> Option<Vec<&Value>> {
    let mut values = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Nil => return Some(values),
            Value::Pair(head, tail) => {
                values.push(head.as_ref());
                cursor = tail.as_ref();
            }
            _ => return None,
        }
    }
}

fn normalize_sens_request(value: &Value) -> Option<NormalizedRequest> {
    if matches!(value, Value::Nil) {
        return None;
    }
    let row = list_values(value).expect("SENS compiler request is a proper list");
    assert_eq!(row.len(), 4, "bounded canonical request has four fields");

    let identity = match row[0] {
        Value::DomainIdentity(identity) => *identity,
        other => panic!("request identity must be exact DomainIdentity, got {other}"),
    };
    let role = match row[1] {
        Value::Symbol(name) => name.to_string(),
        other => panic!("request role must be an abstract symbol, got {other}"),
    };
    let proof_ref = match row[2] {
        Value::String(value) => value.to_string(),
        other => panic!("request proof must be provenance text, got {other}"),
    };
    let provenance = list_values(row[3])
        .expect("request provenance is a proper list")
        .into_iter()
        .map(|item| match item {
            Value::String(value) => value.to_string(),
            other => panic!("provenance item must be text, got {other}"),
        })
        .collect();

    Some(NormalizedRequest {
        identity,
        role,
        proof_ref,
        provenance,
    })
}

fn role_tag(role: CompilerExecutionRole) -> &'static str {
    match role {
        CompilerExecutionRole::SelectorHead => "selector-head",
        CompilerExecutionRole::SelectorTail => "selector-tail",
        CompilerExecutionRole::PairConstruct => "pair-construct",
    }
}

fn host_reference(identity: DomainIdentity, law: &LawProjection) -> Option<NormalizedRequest> {
    let core = identity.core_operation()?;
    let role = compiler_execution_role(core)?;
    Some(NormalizedRequest {
        identity,
        role: role_tag(role).to_string(),
        proof_ref: law.owner_ratification.clone(),
        provenance: provenance(law),
    })
}

fn d3(raw: u8) -> DomainIdentity {
    DomainIdentity::D3(Bija3::from_word(Bit3::new(raw).expect("D3 word")))
}

#[test]
fn selector_corpus_emits_identical_normalized_requests() {
    let law = law_projection();
    let mut runtime = session(&law);
    let mut compared = 0usize;

    for line in CORPUS.lines().filter(|line| !line.is_empty() && !line.starts_with('#')) {
        let fields: Vec<_> = line.split('\t').collect();
        assert_eq!(fields.len(), 6, "compiler corpus row shape changed: {line}");
        let raw = u8::from_str_radix(fields[1], 2).expect("head_bits are exact binary");
        let identity = d3(raw);

        let sens_value = eval_parsed_expressions(&[request(identity)], &mut runtime)
            .unwrap_or_else(|error| panic!("{} SENS request failed: {error:?}", fields[0]))
            .value;
        let sens_request = normalize_sens_request(&sens_value);
        let host_request = host_reference(identity, &law);

        assert_eq!(
            sens_request, host_request,
            "{} host/reference and SENS requests diverged",
            fields[0]
        );
        compared += 1;
    }

    assert!(compared >= 4, "selector corpus must exercise the bounded vertical");
}

#[test]
fn wrong_domain_and_d8_fail_closed_in_both_paths() {
    let law = law_projection();
    let mut runtime = session(&law);
    let cases = [
        DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0100).unwrap())),
        DomainIdentity::D8(CoreD8::from_word(Bit8::new(0b0000_0100).unwrap())),
    ];

    for identity in cases {
        let sens_value = eval_parsed_expressions(&[request(identity)], &mut runtime)
            .expect("unsupported identity returns a normal fail-closed language value")
            .value;
        assert!(normalize_sens_request(&sens_value).is_none());
        assert!(host_reference(identity, &law).is_none());
    }
}

#[test]
fn differential_test_uses_single_corpus_and_no_literal_role_table() {
    assert!(CORPUS.contains("compiler-d3-selector-corpus/1"));
    for forbidden in ["D3:100", "D3:011", "D3:111", "100=>", "011=>", "111=>"] {
        assert!(
            !NUCLEUS.contains(forbidden),
            "production SENS nucleus must not contain literal role mapping {forbidden}"
        );
    }
}
