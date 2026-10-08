//! sens#3804 — host-reference vs SENS-written compiler nucleus parity.
//!
//! This is a differential comparator, never a second compiler.
//! - corpus bytes come from the one SENS-owned machine-readable corpus;
//! - the host side uses `compiler_execution_role` only as differential oracle;
//! - the SENS side executes `compiler-request-from-l1-l5`;
//! - comparison happens before CML/target-specific mechanism binding.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    compiler_execution_role, domain_identity_shape_mechanism, eval_parsed_expressions,
    load_core_library, parse_mixed_exact_domain, parse_canonical_binary, sha256_source, Bija3, Bit3, Bit8,
    CompilerExecutionRole, CoreD8, DomainIdentity, Exactness, Session, Value,
};
use std::fmt;
use std::rc::Rc;

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const LAW: &str = include_str!("../../../knowledge/bija3-l1-l5-structure-projection.json");
const CORPUS: &str = include_str!("../../../contracts/compiler-d3-selector-corpus-v1.tsv");

const MECHANISM_NAME: &str = "__compiler_domain_shape_mechanism";
const LAW_NAME: &str = "__compiler_l1_l5_law";
const PROOF_NAME: &str = "__compiler_l1_l5_proof";
const PROVENANCE_NAME: &str = "__compiler_l1_l5_provenance";

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

#[derive(Debug, Clone, PartialEq, Eq)]
enum RejectionCategory {
    UnadmittedRole,
    WrongDomain,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum NormalizedRequest {
    Request {
        identity: DomainIdentity,
        role: String,
        proof_ref: String,
        authority_sha256: String,
        projection_sha256: String,
        nucleus_sha256: String,
        mechanism_status: &'static str,
        mechanism_ref: Option<String>,
    },
    Reject(RejectionCategory),
}

#[derive(Debug)]
enum HarnessError {
    Bootstrap(String),
    MalformedRequest(String),
}

impl fmt::Display for HarnessError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Bootstrap(message) => write!(formatter, "bootstrap/transport failure: {message}"),
            Self::MalformedRequest(message) => write!(formatter, "malformed SENS request: {message}"),
        }
    }
}

fn quoted_field(text: &str, key: &str) -> String {
    let marker = format!("\"{key}\": \"");
    let start = text
        .find(&marker)
        .unwrap_or_else(|| panic!("missing JSON field {key}"))
        + marker.len();
    let rest = &text[start..];
    let end = rest
        .find('"')
        .unwrap_or_else(|| panic!("unterminated JSON string field {key}"));
    rest[..end].to_string()
}

fn integer_field(text: &str, key: &str) -> u8 {
    let marker = format!("\"{key}\": ");
    let start = text
        .find(&marker)
        .unwrap_or_else(|| panic!("missing JSON integer field {key}"))
        + marker.len();
    let digits = text[start..]
        .chars()
        .take_while(|ch| ch.is_ascii_digit())
        .collect::<String>();
    digits
        .parse::<u8>()
        .unwrap_or_else(|error| panic!("invalid {key}: {error}"))
}

fn l5_spine(text: &str) -> Vec<String> {
    let marker = "\"L5_spine\": [";
    let start = text.find(marker).expect("missing L5_spine") + marker.len();
    let rest = &text[start..];
    let end = rest.find(']').expect("unterminated L5_spine");
    rest[..end]
        .lines()
        .filter_map(|line| {
            let first = line.find('"')?;
            let tail = &line[first + 1..];
            let second = tail.find('"')?;
            Some(tail[..second].to_string())
        })
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

fn sha256_hex(bytes: &[u8]) -> String {
    sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn bit_list(bits: &str) -> Value {
    Value::list(bits.bytes().map(|bit| match bit {
        b'0' => Value::predicate_bit(false),
        b'1' => Value::predicate_bit(true),
        other => panic!("non-binary law projection byte: {other}"),
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

fn provenance_value(law: &LawProjection) -> Value {
    Value::list([
        Value::String(Rc::from(law.authority_sha256.as_str())),
        Value::String(Rc::from(law.projection_sha256.as_str())),
        Value::String(Rc::from(sha256_hex(NUCLEUS.as_bytes()))),
    ])
}

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

fn session(law: &LawProjection) -> Result<Session, HarnessError> {
    let mut session = Session::default();
    load_core_library(&mut session)
        .map_err(|error| HarnessError::Bootstrap(format!("core bootstrap: {error:?}")))?;
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
    let expressions = parse_mixed_exact_domain(NUCLEUS)
        .map_err(|error| HarnessError::Bootstrap(format!("nucleus parse: {error:?}")))?;
    eval_parsed_expressions(&expressions, &mut session)
        .map_err(|error| HarnessError::Bootstrap(format!("nucleus load: {error:?}")))?;
    Ok(session)
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

fn role_tag(role: CompilerExecutionRole) -> &'static str {
    match role {
        CompilerExecutionRole::SelectorHead => "selector-head",
        CompilerExecutionRole::SelectorTail => "selector-tail",
        CompilerExecutionRole::PairConstruct => "pair-construct",
    }
}

fn rejection_category(identity: DomainIdentity) -> RejectionCategory {
    match identity {
        DomainIdentity::D3(_) => RejectionCategory::UnadmittedRole,
        _ => RejectionCategory::WrongDomain,
    }
}

fn host_reference(identity: DomainIdentity, law: &LawProjection) -> NormalizedRequest {
    let role = identity
        .core_operation()
        .and_then(compiler_execution_role);

    match role {
        Some(role) => NormalizedRequest::Request {
            identity,
            role: role_tag(role).to_string(),
            proof_ref: law.owner_ratification.clone(),
            authority_sha256: law.authority_sha256.clone(),
            projection_sha256: law.projection_sha256.clone(),
            nucleus_sha256: sha256_hex(NUCLEUS.as_bytes()),
            // This comparison is intentionally before target-specific lowering.
            mechanism_status: "pre-target-unbound",
            mechanism_ref: None,
        },
        None => NormalizedRequest::Reject(rejection_category(identity)),
    }
}

fn sens_request(
    identity: DomainIdentity,
    session: &mut Session,
) -> Result<NormalizedRequest, HarnessError> {
    let result = eval_parsed_expressions(&[request(identity)], session)
        .map_err(|error| HarnessError::Bootstrap(format!("nucleus request: {error:?}")))?
        .value;

    if matches!(result, Value::Nil) {
        return Ok(NormalizedRequest::Reject(rejection_category(identity)));
    }

    let row = list_values(&result)
        .ok_or_else(|| HarnessError::MalformedRequest(format!("not a proper list: {result}")))?;
    if row.len() != 4 {
        return Err(HarnessError::MalformedRequest(format!(
            "expected four request fields, got {}",
            row.len()
        )));
    }

    let observed_identity = match row[0] {
        Value::DomainIdentity(value) => *value,
        other => {
            return Err(HarnessError::MalformedRequest(format!(
                "identity field is not DomainIdentity: {other}"
            )))
        }
    };
    let observed_role = match row[1] {
        Value::Symbol(value) => value.as_ref().to_string(),
        other => {
            return Err(HarnessError::MalformedRequest(format!(
                "role field is not symbol: {other}"
            )))
        }
    };
    let proof_ref = match row[2] {
        Value::String(value) => value.as_ref().to_string(),
        other => {
            return Err(HarnessError::MalformedRequest(format!(
                "proof field is not string: {other}"
            )))
        }
    };
    let provenance = list_values(row[3])
        .ok_or_else(|| HarnessError::MalformedRequest("provenance is not a list".into()))?;
    if provenance.len() != 3 {
        return Err(HarnessError::MalformedRequest(format!(
            "expected three provenance fields, got {}",
            provenance.len()
        )));
    }
    let string_field = |value: &Value, name: &str| -> Result<String, HarnessError> {
        match value {
            Value::String(text) => Ok(text.as_ref().to_string()),
            other => Err(HarnessError::MalformedRequest(format!(
                "{name} is not string: {other}"
            ))),
        }
    };

    Ok(NormalizedRequest::Request {
        identity: observed_identity,
        role: observed_role,
        proof_ref,
        authority_sha256: string_field(provenance[0], "authority sha")?,
        projection_sha256: string_field(provenance[1], "projection sha")?,
        nucleus_sha256: string_field(provenance[2], "nucleus sha")?,
        mechanism_status: "pre-target-unbound",
        mechanism_ref: None,
    })
}

fn collect_identities(expr: &Expr, out: &mut Vec<DomainIdentity>) {
    match &expr.kind {
        ExprKind::DomainIdentity(identity) => {
            if !out.contains(identity) {
                out.push(*identity);
            }
        }
        ExprKind::List(items) => {
            for item in items.iter() {
                collect_identities(item, out);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_identities(head, out);
            collect_identities(tail, out);
        }
        ExprKind::DomainCall(identity, args) => {
            let exact = DomainIdentity::from_source_word(identity.source_word());
            if !out.contains(&exact) {
                out.push(exact);
            }
            for arg in args.iter() {
                collect_identities(arg, out);
            }
        }
        ExprKind::Sid(_)
        | ExprKind::Call(_, _)
        | ExprKind::Number(_, _)
        | ExprKind::Rational(_)
        | ExprKind::BinaryNumber(_)
        | ExprKind::NumericBuffer(_)
        | ExprKind::String(_)
        | ExprKind::Symbol(_)
        | ExprKind::Local { .. } => {}
    }
}

fn corpus_identities() -> Vec<DomainIdentity> {
    let mut out = Vec::new();

    for line in CORPUS.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        let fields = line.split('\t').collect::<Vec<_>>();
        assert_eq!(fields.len(), 6, "shared compiler corpus row shape");
        let parsed = parse_canonical_binary(fields[2])
            .unwrap_or_else(|error| panic!("{} canonical parse failed: {error:?}", fields[0]));
        for expr in &parsed {
            collect_identities(expr, &mut out);
        }
    }

    out
}

#[test]
fn host_reference_and_sens_nucleus_emit_identical_normalized_requests() {
    let law = law_projection();
    let mut session = session(&law)
        .unwrap_or_else(|error| panic!("{error}"));

    let identities = corpus_identities();
    assert!(
        identities.len() >= 3,
        "shared corpus must expose the three bounded callable roles; structural empty is data"
    );

    for identity in identities {
        let host = host_reference(identity, &law);
        let sens = sens_request(identity, &mut session)
            .unwrap_or_else(|error| panic!("{error}"));

        assert_eq!(
            sens, host,
            "semantic mismatch for exact identity {identity}"
        );
    }
}

#[test]
fn wrong_domain_is_a_named_rejection_not_a_transport_failure() {
    let law = law_projection();
    let mut session = session(&law)
        .unwrap_or_else(|error| panic!("{error}"));

    let d8 = DomainIdentity::D8(CoreD8::from_word(
        Bit8::new(0b0000_0100).expect("D8 exact word"),
    ));

    let host = host_reference(d8, &law);
    let sens = sens_request(d8, &mut session)
        .unwrap_or_else(|error| panic!("{error}"));

    assert_eq!(host, NormalizedRequest::Reject(RejectionCategory::WrongDomain));
    assert_eq!(sens, host, "semantic mismatch in D8 fail-closed category");
}

#[test]
fn comparator_reuses_shared_corpus_and_the_named_differential_oracle() {
    let source = include_str!("compiler_nucleus_diff.rs");
    assert!(source.contains("compiler-d3-selector-corpus-v1.tsv"));
    assert!(source.contains("compiler_execution_role"));
    let raw_dispatch = ["match ", "raw"].concat();
    assert!(
        !source.contains(&raw_dispatch),
        "differential comparator must not grow a raw coordinate dispatch"
    );
}

#[test]
fn unadmitted_d3_is_a_named_rejection_not_a_transport_failure() {
    let law = law_projection();
    let mut session = session(&law).unwrap_or_else(|error| panic!("{error}"));
    let empty_identity =
        DomainIdentity::D3(Bija3::from_word(Bit3::new(0).expect("exact D3 zero")));

    let host = host_reference(empty_identity, &law);
    let sens = sens_request(empty_identity, &mut session)
        .unwrap_or_else(|error| panic!("{error}"));

    assert_eq!(
        host,
        NormalizedRequest::Reject(RejectionCategory::UnadmittedRole)
    );
    assert_eq!(sens, host, "semantic mismatch in unadmitted D3 category");
}
