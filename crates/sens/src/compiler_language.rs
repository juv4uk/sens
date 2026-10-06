//! Transport adapter from host/compiler callers into the SENS-written
//! compiler-role law.
//!
//! Semantic direction is intentionally one-way:
//!
//!   exact DomainIdentity
//!     -> SENS compiler nucleus + generated L1-L5 structural projection
//!     -> abstract CompilerExecutionRole
//!
//! This Rust module owns only bootstrap transport, projection integrity checks,
//! SENS evaluation, and representation conversion of the already-derived role.
//! It must never decide identity -> role from domain coordinates.

use crate::{
    domain_identity_predicate_mechanism, domain_identity_shape_mechanism,
    eval_parsed_expressions, eval_program, load_core_library, lower_program, parse, sha256_source,
    wire_decode_program, wire_encode_program, CompilerExecutionRole, CompilerLoweringRole,
    CoreDomainIdentity, DomainIdentity, ErrorKind, Exactness, Expr, ExprKind, LanguageError,
    Session, Span, Value,
};
use std::rc::Rc;

const COMPILER_NUCLEUS_SOURCE: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const LANGUAGE_CONTRACT: &str = include_str!("../../../language-contract.lisp");

pub const COMPILER_ROLE_LAW_REF: &str =
    "lib/compiler-nucleus.lisp:compiler-lowering-role-from-laws";
pub const COMPILER_D3_PROOF_REF: &str = "contracts/bija3-l1-l5-ratification.lisp";
pub const COMPILER_D4_PROOF_REF: &str = "contracts/d4-bootstrap-ratification.lisp";
pub const COMPILER_AUTHORITY_PATH: &str = "language-contract.lisp";
pub const COMPILER_CONTRACT_VERSION: &str = "11.6";

/// SENS-owned semantic input for one current compiler identity.
///
/// This value contains only language authority facts. It deliberately contains
/// no target/backend mechanism identifier and no repository checkout revision;
/// a serializer may attach its exact source revision as transport provenance.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CompilerSemanticInput {
    pub identity: CoreDomainIdentity,
    pub lowering_role: CompilerLoweringRole,
    pub authority_ref: &'static str,
    pub proof_ref: &'static str,
    pub semantic_status: &'static str,
    pub authority_path: &'static str,
    pub authority_sha256: String,
    pub language_contract_version: &'static str,
}
const LAW_PROJECTION: &str =
    include_str!("../../../knowledge/bija3-l1-l5-structure-projection.json");
const LAW_AUTHORITY: &str = include_str!("../../../contracts/bija3-l1-l5-ratification.lisp");
const D4_LAW_PROJECTION: &str =
    include_str!("../../../knowledge/d4-bootstrap-compiler-structure-projection.json");
const D4_LAW_AUTHORITY: &str = include_str!("../../../contracts/d4-bootstrap-ratification.lisp");

const SHAPE_MECHANISM_NAME: &str = "__compiler_domain_shape_mechanism";
const DOMAIN_PREDICATE_MECHANISM_NAME: &str = "__compiler_domain_identity_predicate";
const LAW_VALUE_NAME: &str = "__compiler_l1_l5_law";
const D4_LAW_VALUE_NAME: &str = "__compiler_d4_bootstrap_law";
const PROGRAM_AST_VALUE_NAME: &str = "__compiler_program_ast";
const D3_PROOF_VALUE_NAME: &str = "__compiler_d3_proof";
const D4_PROOF_VALUE_NAME: &str = "__compiler_d4_proof";
const PROGRAM_PROVENANCE_VALUE_NAME: &str = "__compiler_program_provenance";

fn invalid_projection(message: impl Into<String>) -> LanguageError {
    LanguageError::new(ErrorKind::InvalidForm, message, Span::default())
}

fn quoted_json_string(source: &str, key: &str) -> Result<String, LanguageError> {
    let marker = format!("\"{key}\": \"");
    let start = source
        .find(&marker)
        .ok_or_else(|| invalid_projection(format!("missing generated law field: {key}")))?
        + marker.len();
    let rest = &source[start..];
    let end = rest
        .find('"')
        .ok_or_else(|| invalid_projection(format!("unterminated generated law field: {key}")))?;
    Ok(rest[..end].to_string())
}

fn projection_width() -> Result<usize, LanguageError> {
    let domain = LAW_PROJECTION
        .find("\"domain\"")
        .ok_or_else(|| invalid_projection("generated law projection has no domain block"))?;
    let rest = &LAW_PROJECTION[domain..];
    let marker = "\"width\": ";
    let start = rest
        .find(marker)
        .ok_or_else(|| invalid_projection("generated law projection has no domain width"))?
        + marker.len();
    let digits = rest[start..]
        .chars()
        .take_while(|ch| ch.is_ascii_digit())
        .collect::<String>();
    if digits.is_empty() {
        return Err(invalid_projection("generated law domain width is not numeric"));
    }
    digits
        .parse()
        .map_err(|_| invalid_projection("generated law domain width is invalid"))
}

fn projection_width_from(source: &str) -> Result<usize, LanguageError> {
    let domain = source
        .find("\"domain\"")
        .ok_or_else(|| invalid_projection("generated law projection has no domain block"))?;
    let rest = &source[domain..];
    let marker = "\"width\": ";
    let start = rest
        .find(marker)
        .ok_or_else(|| invalid_projection("generated law projection has no domain width"))?
        + marker.len();
    let digits = rest[start..]
        .chars()
        .take_while(|ch| ch.is_ascii_digit())
        .collect::<String>();
    if digits.is_empty() {
        return Err(invalid_projection("generated law domain width is not numeric"));
    }
    digits
        .parse()
        .map_err(|_| invalid_projection("generated law domain width is invalid"))
}

fn projection_string_array(source: &str, key: &str) -> Result<Vec<String>, LanguageError> {
    let marker = format!("\"{key}\": [");
    let start = source
        .find(&marker)
        .ok_or_else(|| invalid_projection(format!("generated law projection has no {key} array")))?
        + marker.len();
    let tail = &source[start..];
    let end = tail
        .find(']')
        .ok_or_else(|| invalid_projection(format!("generated {key} array is unterminated")))?;
    Ok(tail[..end]
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(|item| item.trim_matches('"').to_string())
        .collect())
}

fn projection_spine() -> Result<Vec<String>, LanguageError> {
    let marker = "\"L5_spine\": [";
    let start = LAW_PROJECTION
        .find(marker)
        .ok_or_else(|| invalid_projection("generated law projection has no L5 spine"))?
        + marker.len();
    let tail = &LAW_PROJECTION[start..];
    let end = tail
        .find(']')
        .ok_or_else(|| invalid_projection("generated L5 spine is unterminated"))?;
    Ok(tail[..end]
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(|item| item.trim_matches('"').to_string())
        .collect())
}

fn sha256_hex(bytes: &[u8]) -> String {
    sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn authority_sha256_from(projection: &str) -> Result<String, LanguageError> {
    let authority = projection
        .find("\"semantic_authority\"")
        .ok_or_else(|| invalid_projection("generated law projection has no authority provenance"))?;
    quoted_json_string(&projection[authority..], "sha256")
}

fn verify_projection_authority(
    projection: &str,
    authority: &str,
) -> Result<(), LanguageError> {
    let expected_authority_sha = authority_sha256_from(projection)?;
    let actual_authority_sha = sha256_hex(authority.as_bytes());
    if expected_authority_sha != actual_authority_sha {
        return Err(invalid_projection(
            "generated structural projection is stale against its ratified authority",
        ));
    }
    Ok(())
}

fn bit_list(bits: &str, width: usize) -> Result<Value, LanguageError> {
    if bits.len() != width {
        return Err(invalid_projection(format!(
            "generated law bit width mismatch: expected {width}, got {}",
            bits.len()
        )));
    }
    let values = bits
        .bytes()
        .map(|bit| match bit {
            b'0' => Ok(Value::predicate_bit(false)),
            b'1' => Ok(Value::predicate_bit(true)),
            other => Err(invalid_projection(format!(
                "generated law contains non-binary byte: {other}"
            ))),
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Value::list(values))
}

fn compiler_l1_l5_law_value() -> Result<Value, LanguageError> {
    if !LAW_PROJECTION.contains("\"status\": \"generated-projection-only\"") {
        return Err(invalid_projection(
            "compiler law input is not marked generated-projection-only",
        ));
    }
    if !LAW_PROJECTION.contains("\"compiler_role_table\": false") {
        return Err(invalid_projection(
            "generated law projection must forbid a compiler role table",
        ));
    }
    for forbidden in ["SelectorHead", "SelectorTail", "PairConstruct"] {
        if LAW_PROJECTION.contains(forbidden) {
            return Err(invalid_projection(format!(
                "generated structural law projection precomputes compiler role {forbidden}"
            )));
        }
    }

    verify_projection_authority(LAW_PROJECTION, LAW_AUTHORITY)?;

    let width = projection_width()?;
    let empty = quoted_json_string(LAW_PROJECTION, "L1_empty")?;
    let mask = quoted_json_string(LAW_PROJECTION, "L4_dual_xor_mask")?;
    let spine = projection_spine()?;
    if spine.len() != 4 {
        return Err(invalid_projection(format!(
            "generated L5 spine must contain four structural nodes, got {}",
            spine.len()
        )));
    }

    Ok(Value::list([
        Value::Number(width as f64, Exactness::Exact),
        bit_list(&empty, width)?,
        bit_list(&mask, width)?,
        Value::list(
            spine
                .iter()
                .map(|bits| bit_list(bits, width))
                .collect::<Result<Vec<_>, _>>()?,
        ),
    ]))
}

fn compiler_d4_bootstrap_law_value() -> Result<Value, LanguageError> {
    if !D4_LAW_PROJECTION.contains("\"status\": \"generated-projection-only\"") {
        return Err(invalid_projection(
            "D4 compiler law input is not marked generated-projection-only",
        ));
    }
    for required_false in [
        "\"compiler_role_table\": false",
        "\"backend_mechanism_table\": false",
        "\"human_name_routing\": false",
        "\"d8_admission\": false",
    ] {
        if !D4_LAW_PROJECTION.contains(required_false) {
            return Err(invalid_projection(format!(
                "D4 structural projection is missing non-authority guard: {required_false}"
            )));
        }
    }
    for forbidden in [
        "LambdaForm",
        "DefineForm",
        "lambda-form",
        "define-form",
        "CompilerLoweringRole",
    ] {
        if D4_LAW_PROJECTION.contains(forbidden) {
            return Err(invalid_projection(format!(
                "D4 structural projection precomputes compiler role {forbidden}"
            )));
        }
    }

    verify_projection_authority(D4_LAW_PROJECTION, D4_LAW_AUTHORITY)?;

    let width = projection_width_from(D4_LAW_PROJECTION)?;
    if width != 4 {
        return Err(invalid_projection(format!(
            "D4 bootstrap projection must have exact width 4, got {width}"
        )));
    }

    let parent = quoted_json_string(D4_LAW_PROJECTION, "parent_bits")?;
    if parent.len() + 1 != width {
        return Err(invalid_projection(
            "D4 bootstrap parent must be the exact one-bit-shorter fibre prefix",
        ));
    }

    let children = projection_string_array(D4_LAW_PROJECTION, "children")?;
    if children.len() != 2 {
        return Err(invalid_projection(format!(
            "D4 bootstrap fibre must have exactly two ordered children, got {}",
            children.len()
        )));
    }
    for child in &children {
        if child.len() != width || !child.starts_with(&parent) {
            return Err(invalid_projection(
                "D4 bootstrap child does not preserve its exact D3 parent prefix",
            ));
        }
    }

    Ok(Value::list([
        Value::Number(width as f64, Exactness::Exact),
        bit_list(&parent, width - 1)?,
        Value::list(
            children
                .iter()
                .map(|bits| bit_list(bits, width))
                .collect::<Result<Vec<_>, _>>()?,
        ),
    ]))
}

fn symbol(name: &str) -> Expr {
    Expr {
        kind: ExprKind::Symbol(Rc::from(name)),
        span: Span::default(),
    }
}

fn language_role_call(identity: CoreDomainIdentity) -> Expr {
    let exact_identity = DomainIdentity::from_source_word(identity.source_word());
    Expr {
        kind: ExprKind::List(Rc::from(
            vec![
                symbol("compiler-lowering-role-from-laws"),
                symbol(SHAPE_MECHANISM_NAME),
                Expr {
                    kind: ExprKind::DomainIdentity(exact_identity),
                    span: Span::default(),
                },
                symbol(LAW_VALUE_NAME),
                symbol(D4_LAW_VALUE_NAME),
            ]
            .into_boxed_slice(),
        )),
        span: Span::default(),
    }
}

fn decode_language_lowering_role(
    value: &Value,
) -> Result<Option<CompilerLoweringRole>, LanguageError> {
    match value {
        Value::Nil => Ok(None),
        Value::Symbol(name) if name.as_ref() == "quote-form" => {
            Ok(Some(CompilerLoweringRole::QuoteForm))
        }
        Value::Symbol(name) if name.as_ref() == "atom-predicate" => {
            Ok(Some(CompilerLoweringRole::AtomPredicate))
        }
        Value::Symbol(name) if name.as_ref() == "selector-tail" => {
            Ok(Some(CompilerLoweringRole::SelectorTail))
        }
        Value::Symbol(name) if name.as_ref() == "selector-head" => {
            Ok(Some(CompilerLoweringRole::SelectorHead))
        }
        Value::Symbol(name) if name.as_ref() == "atom-equality" => {
            Ok(Some(CompilerLoweringRole::AtomEquality))
        }
        Value::Symbol(name) if name.as_ref() == "cond-form" => {
            Ok(Some(CompilerLoweringRole::CondForm))
        }
        Value::Symbol(name) if name.as_ref() == "pair-construct" => {
            Ok(Some(CompilerLoweringRole::PairConstruct))
        }
        Value::Symbol(name) if name.as_ref() == "lambda-form" => {
            Ok(Some(CompilerLoweringRole::LambdaForm))
        }
        Value::Symbol(name) if name.as_ref() == "define-form" => {
            Ok(Some(CompilerLoweringRole::DefineForm))
        }
        Value::Symbol(name) => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!("SENS compiler nucleus returned unknown abstract role: {name}"),
            Span::default(),
        )),
        other => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!("SENS compiler nucleus returned non-role value: {other}"),
            Span::default(),
        )),
    }
}

/// Derive the complete current compiler lowering role by executing the
/// SENS-owned compiler law over the ratified D3 and D4 structural inputs.
pub fn compiler_lowering_role_from_sens(
    identity: CoreDomainIdentity,
) -> Result<Option<CompilerLoweringRole>, LanguageError> {
    let mut session = Session::default();
    load_core_library(&mut session)?;

    session
        .environment
        .define(SHAPE_MECHANISM_NAME, domain_identity_shape_mechanism());
    session.environment.define(
        DOMAIN_PREDICATE_MECHANISM_NAME,
        domain_identity_predicate_mechanism(),
    );
    session
        .environment
        .define(LAW_VALUE_NAME, compiler_l1_l5_law_value()?);
    session
        .environment
        .define(D4_LAW_VALUE_NAME, compiler_d4_bootstrap_law_value()?);

    eval_program(COMPILER_NUCLEUS_SOURCE, &mut session)?;

    let result = eval_parsed_expressions(&[language_role_call(identity)], &mut session)?.value;
    decode_language_lowering_role(&result)
}

/// Backward-compatible three-role view used by the already-landed selector/pair
/// compiler bridge. It delegates to the same full SENS-owned role law and never
/// reconstructs identity-to-role meaning in Rust.
/// Produce the canonical proof-carrying compiler semantic input for one exact
/// current identity.
///
/// Role meaning and D3/D4 proof ownership are selected inside SENS. Downstream
/// consumers may verify and bind a private mechanism, but must not reconstruct
/// either fact from coordinates, names, or a legacy callable identity.
pub fn compiler_semantic_input_from_sens(
    identity: CoreDomainIdentity,
) -> Result<Option<CompilerSemanticInput>, LanguageError> {
    let Some(lowering_role) = compiler_lowering_role_from_sens(identity)? else {
        return Ok(None);
    };

    let proof_ref = match lowering_role {
        CompilerLoweringRole::LambdaForm | CompilerLoweringRole::DefineForm => {
            COMPILER_D4_PROOF_REF
        }
        CompilerLoweringRole::QuoteForm
        | CompilerLoweringRole::AtomPredicate
        | CompilerLoweringRole::SelectorTail
        | CompilerLoweringRole::SelectorHead
        | CompilerLoweringRole::AtomEquality
        | CompilerLoweringRole::CondForm
        | CompilerLoweringRole::PairConstruct => COMPILER_D3_PROOF_REF,
    };

    Ok(Some(CompilerSemanticInput {
        identity,
        lowering_role,
        authority_ref: COMPILER_ROLE_LAW_REF,
        proof_ref,
        semantic_status: "current",
        authority_path: COMPILER_AUTHORITY_PATH,
        authority_sha256: sha256_hex(LANGUAGE_CONTRACT.as_bytes()),
        language_contract_version: COMPILER_CONTRACT_VERSION,
    }))
}

fn compiler_program_data_expr_value(expr: &Expr) -> Result<Value, LanguageError> {
    match &expr.kind {
        ExprKind::Number(value, exactness) => Ok(Value::Number(*value, *exactness)),
        ExprKind::Rational(value) => Ok(Value::Rational(value.clone())),
        ExprKind::BinaryNumber(value) => Ok(Value::BinaryNumber(value.clone())),
        ExprKind::NumericBuffer(value) => Ok(Value::NumericBuffer(value.clone())),
        ExprKind::DomainIdentity(identity) => Ok(Value::DomainIdentity(*identity)),
        ExprKind::String(value) => Ok(Value::String(value.clone())),
        ExprKind::Symbol(value) => Ok(Value::Symbol(value.clone())),
        ExprKind::List(items) => Ok(Value::list(
            items
                .iter()
                .map(compiler_program_data_expr_value)
                .collect::<Result<Vec<_>, _>>()?,
        )),
        ExprKind::Pair(head, tail) => Ok(Value::Pair(
            Rc::new(compiler_program_data_expr_value(head)?),
            Rc::new(compiler_program_data_expr_value(tail)?),
        )),
        ExprKind::DomainCall(identity, arguments) => {
            // Canonical SW1 decode currently exposes DomainCall as a source-shaped
            // list. Keep this mechanical fallback so representation stays total
            // if an in-memory caller bypasses the round-trip.
            let mut values = Vec::with_capacity(arguments.len() + 1);
            values.push(Value::DomainIdentity(DomainIdentity::from_source_word(
                identity.source_word(),
            )));
            values.extend(
                arguments
                    .iter()
                    .map(compiler_program_data_expr_value)
                    .collect::<Result<Vec<_>, _>>()?,
            );
            Ok(Value::list(values))
        }
        ExprKind::Sid(_) | ExprKind::Call(_, _) => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "legacy Sid8/Call cannot enter compiler-program-data/1",
            expr.span,
        )),
        ExprKind::Local { .. } => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "resolved lexical Local cannot enter source-shaped compiler-program-data/1",
            expr.span,
        )),
    }
}

fn compiler_program_data_value(expressions: &[Expr]) -> Result<Value, LanguageError> {
    let wire = wire_encode_program(expressions);
    let decoded = wire_decode_program(&wire).ok_or_else(|| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            "canonical compiler-program-data/1 SW1 round-trip failed",
            Span::default(),
        )
    })?;

    Ok(Value::list(
        decoded
            .iter()
            .map(compiler_program_data_expr_value)
            .collect::<Result<Vec<_>, _>>()?,
    ))
}

fn compiler_program_provenance_value(source: &str) -> Value {
    Value::list([
        Value::String(Rc::from(sha256_hex(source.as_bytes()))),
        Value::String(Rc::from(sha256_hex(COMPILER_NUCLEUS_SOURCE.as_bytes()))),
        Value::String(Rc::from(sha256_hex(LANGUAGE_CONTRACT.as_bytes()))),
        Value::String(Rc::from(COMPILER_CONTRACT_VERSION)),
    ])
}

fn compiler_program_artifact_call() -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(
            vec![
                symbol("compiler-compile-program"),
                symbol(SHAPE_MECHANISM_NAME),
                symbol(DOMAIN_PREDICATE_MECHANISM_NAME),
                symbol(PROGRAM_AST_VALUE_NAME),
                symbol(LAW_VALUE_NAME),
                symbol(D4_LAW_VALUE_NAME),
                symbol(D3_PROOF_VALUE_NAME),
                symbol(D4_PROOF_VALUE_NAME),
                symbol(PROGRAM_PROVENANCE_VALUE_NAME),
            ]
            .into_boxed_slice(),
        )),
        span: Span::default(),
    }
}

fn compiler_program_artifact_from_expressions(
    lowered: &[Expr],
    provenance_source: &str,
) -> Result<Value, LanguageError> {
    let mut session = Session::default();
    load_core_library(&mut session)?;

    session
        .environment
        .define(SHAPE_MECHANISM_NAME, domain_identity_shape_mechanism());
    session
        .environment
        .define(LAW_VALUE_NAME, compiler_l1_l5_law_value()?);
    session
        .environment
        .define(D4_LAW_VALUE_NAME, compiler_d4_bootstrap_law_value()?);
    session.environment.define(
        D3_PROOF_VALUE_NAME,
        Value::String(Rc::from(COMPILER_D3_PROOF_REF)),
    );
    session.environment.define(
        D4_PROOF_VALUE_NAME,
        Value::String(Rc::from(COMPILER_D4_PROOF_REF)),
    );
    session.environment.define(
        PROGRAM_PROVENANCE_VALUE_NAME,
        compiler_program_provenance_value(provenance_source),
    );
    session.environment.define(
        PROGRAM_AST_VALUE_NAME,
        compiler_program_data_value(lowered)?,
    );

    eval_program(COMPILER_NUCLEUS_SOURCE, &mut session)?;
    Ok(eval_parsed_expressions(&[compiler_program_artifact_call()], &mut session)?.value)
}

/// Compile one exact current SENS source bundle into the backend-neutral
/// whole-program request artifact by executing the SENS-written compiler body.
///
/// Rust owns only parse/lower -> canonical compiler-program-data/1 SW1
/// encode/decode transport and bootstrap installation of generated structural
/// laws. It never chooses an identity's compiler role, proof, or traversal policy.
pub fn compiler_program_artifact_from_sens(source: &str) -> Result<Value, LanguageError> {
    let parsed = parse(source)?;
    let lowered = lower_program(&parsed);
    compiler_program_artifact_from_expressions(&lowered, source)
}

pub fn compiler_execution_role_from_sens(
    identity: CoreDomainIdentity,
) -> Result<Option<CompilerExecutionRole>, LanguageError> {
    match compiler_lowering_role_from_sens(identity)? {
        Some(CompilerLoweringRole::SelectorHead) => {
            Ok(Some(CompilerExecutionRole::SelectorHead))
        }
        Some(CompilerLoweringRole::SelectorTail) => {
            Ok(Some(CompilerExecutionRole::SelectorTail))
        }
        Some(CompilerLoweringRole::PairConstruct) => {
            Ok(Some(CompilerExecutionRole::PairConstruct))
        }
        Some(_) | None => Ok(None),
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    fn d3(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D3(
            crate::Bija3::from_word(crate::Bit3::new(raw).expect("D3 test word")),
        )
    }

    fn d4(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D4(
            crate::CoreD4::from_word(crate::Bit4::new(raw).expect("D4 test word")),
        )
    }

    #[test]
    fn stale_law_authority_is_a_bootstrap_failure_before_role_execution() {
        let stale_authority = format!("{LAW_AUTHORITY}\n; parity-test-stale-authority");
        let error = verify_projection_authority(LAW_PROJECTION, &stale_authority)
            .expect_err("stale authority must be rejected before SENS role execution");

        assert!(
            error
                .to_string()
                .contains("stale against its ratified authority"),
            "unexpected stale-projection error: {error}"
        );
    }

    #[test]
    fn d4_projection_authority_is_verified_before_role_execution() {
        let stale_authority = format!("{D4_LAW_AUTHORITY}\n; parity-test-stale-authority");
        let error = verify_projection_authority(D4_LAW_PROJECTION, &stale_authority)
            .expect_err("stale D4 authority must be rejected before SENS role execution");

        assert!(
            error
                .to_string()
                .contains("stale against its ratified authority"),
            "unexpected D4 stale-projection error: {error}"
        );
    }

    #[test]
    fn semantic_input_api_owns_law_proof_and_root_authority_facts() {
        let d3_input = compiler_semantic_input_from_sens(d3(0b010))
            .expect("D3 semantic input")
            .expect("ATOM is in compiler closure");
        assert_eq!(d3_input.lowering_role, CompilerLoweringRole::AtomPredicate);
        assert_eq!(d3_input.authority_ref, COMPILER_ROLE_LAW_REF);
        assert_eq!(d3_input.proof_ref, COMPILER_D3_PROOF_REF);
        assert_eq!(d3_input.semantic_status, "current");
        assert_eq!(d3_input.authority_path, "language-contract.lisp");
        assert_eq!(d3_input.authority_sha256.len(), 64);
        assert_eq!(d3_input.language_contract_version, "11.6");

        let d4_input = compiler_semantic_input_from_sens(d4(0b0010))
            .expect("D4 semantic input")
            .expect("LAMBDA is in compiler closure");
        assert_eq!(d4_input.lowering_role, CompilerLoweringRole::LambdaForm);
        assert_eq!(d4_input.authority_ref, COMPILER_ROLE_LAW_REF);
        assert_eq!(d4_input.proof_ref, COMPILER_D4_PROOF_REF);
        assert_eq!(d4_input.authority_sha256, d3_input.authority_sha256);

        assert!(
            compiler_semantic_input_from_sens(d3(0b000))
                .expect("D3 empty transport")
                .is_none()
        );
        let d8 = CoreDomainIdentity::D8(crate::CoreD8::from_word(
            crate::Bit8::new(0b0000_0010).expect("D8 word"),
        ));
        assert!(
            compiler_semantic_input_from_sens(d8)
                .expect("D8 must fail closed as no compiler input")
                .is_none()
        );
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

    fn domain_call(identity: CoreDomainIdentity, arguments: Vec<Expr>) -> Expr {
        Expr {
            kind: ExprKind::DomainCall(identity, Rc::from(arguments.into_boxed_slice())),
            span: Span::default(),
        }
    }

    fn artifact_requests(value: &Value) -> Option<Vec<&Value>> {
        let outer = list_values(value)?;
        if outer.len() != 2 {
            return None;
        }
        if !matches!(outer[0], Value::Symbol(name) if name.as_ref() == "compiler-compilation-artifact/1") {
            return None;
        }
        list_values(outer[1])
    }

    #[test]
    fn whole_program_adapter_reuses_ratified_sw1_and_contains_no_second_ast_tags() {
        let source = include_str!("compiler_language.rs");
        assert!(source.contains("wire_encode_program(expressions)"));
        assert!(source.contains("wire_decode_program(&wire)"));
        assert!(source.contains("domain_identity_predicate_mechanism()"));

        for forbidden in [
            ["Value::Symbol(Rc::from(", "\"domain-call\""].concat(),
            ["Value::Symbol(Rc::from(", "\"children\""].concat(),
        ] {
            assert!(
                !source.contains(&forbidden),
                "compiler bootstrap adapter invented a second AST wire tag: {forbidden}"
            );
        }
    }

    #[test]
    fn whole_program_compiler_walks_real_nucleus_and_reaches_all_nine_roles() {
        let artifact = compiler_program_artifact_from_sens(COMPILER_NUCLEUS_SOURCE)
            .expect("whole current compiler nucleus artifact");
        let second = compiler_program_artifact_from_sens(COMPILER_NUCLEUS_SOURCE)
            .expect("whole current compiler nucleus artifact is deterministic");
        assert_eq!(artifact, second, "whole-program artifact must be deterministic");

        let requests = artifact_requests(&artifact).expect("versioned whole-program artifact");
        assert!(
            requests.len() >= 9,
            "real compiler nucleus must emit at least the nine current semantic requests"
        );

        let mut roles = std::collections::HashSet::new();
        let mut saw_d3_proof = false;
        let mut saw_d4_proof = false;
        for request in requests {
            let row = list_values(request).expect("compiler request row");
            assert_eq!(row.len(), 4);
            match row[0] {
                Value::DomainIdentity(identity) => {
                    assert!(
                        matches!(identity.width(), 3 | 4),
                        "whole current compiler artifact admitted unexpected domain {identity:?}"
                    );
                }
                other => panic!("request identity is not exact DomainIdentity: {other}"),
            }
            match row[1] {
                Value::Symbol(role) => {
                    roles.insert(role.to_string());
                }
                other => panic!("request role is not a symbol: {other}"),
            }
            match row[2] {
                Value::String(proof) if proof.as_ref() == COMPILER_D3_PROOF_REF => {
                    saw_d3_proof = true;
                }
                Value::String(proof) if proof.as_ref() == COMPILER_D4_PROOF_REF => {
                    saw_d4_proof = true;
                }
                other => panic!("unexpected compiler proof: {other}"),
            }
        }

        let expected = [
            "quote-form",
            "atom-predicate",
            "selector-tail",
            "selector-head",
            "atom-equality",
            "cond-form",
            "pair-construct",
            "lambda-form",
            "define-form",
        ]
        .into_iter()
        .map(str::to_string)
        .collect::<std::collections::HashSet<_>>();
        assert_eq!(roles, expected);
        assert!(saw_d3_proof && saw_d4_proof);
    }

    #[test]
    fn whole_program_compiler_owns_quote_opacity() {
        let quoted_d8 = domain_call(
            d3(0b001),
            vec![domain_call(
                CoreDomainIdentity::D8(crate::CoreD8::from_word(
                    crate::Bit8::new(0b0000_0100).unwrap(),
                )),
                vec![],
            )],
        );
        let artifact = compiler_program_artifact_from_expressions(
            &[quoted_d8],
            "(synthetic quote-opacity witness)",
        )
        .expect("QUOTE child is opaque compiler data");
        let requests = artifact_requests(&artifact).expect("QUOTE artifact");
        assert_eq!(requests.len(), 1, "quoted D8 child must not be traversed");
        let row = list_values(requests[0]).unwrap();
        assert!(matches!(row[1], Value::Symbol(role) if role.as_ref() == "quote-form"));
    }

    #[test]
    fn same_payload_wrong_domain_and_d8_fail_closed_in_whole_program_compile() {
        let d3_car = domain_call(d3(0b100), vec![]);
        let d3_artifact = compiler_program_artifact_from_expressions(
            &[d3_car],
            "(synthetic D3 payload witness)",
        )
        .expect("D3 CAR compiler program");
        assert!(artifact_requests(&d3_artifact).is_some());

        let d4_same_payload = domain_call(d4(0b0100), vec![]);
        let wrong_domain = compiler_program_artifact_from_expressions(
            &[d4_same_payload],
            "(synthetic D4 same-payload witness)",
        )
        .expect("unsupported D4 identity returns fail-closed language value");
        assert!(matches!(wrong_domain, Value::Symbol(ref name) if name.as_ref() == "compiler-failure"));

        let d8 = domain_call(
            CoreDomainIdentity::D8(crate::CoreD8::from_word(
                crate::Bit8::new(0b0000_0100).unwrap(),
            )),
            vec![],
        );
        let d8_result = compiler_program_artifact_from_expressions(
            &[d8],
            "(synthetic D8 witness)",
        )
        .expect("D8 returns fail-closed language value");
        assert!(matches!(d8_result, Value::Symbol(ref name) if name.as_ref() == "compiler-failure"));
    }

    #[test]
    fn current_nucleus_roles_are_derived_by_the_single_sens_owned_law() {
        let expected = [
            (d3(0b001), CompilerLoweringRole::QuoteForm),
            (d3(0b010), CompilerLoweringRole::AtomPredicate),
            (d3(0b011), CompilerLoweringRole::SelectorTail),
            (d3(0b100), CompilerLoweringRole::SelectorHead),
            (d3(0b101), CompilerLoweringRole::AtomEquality),
            (d3(0b110), CompilerLoweringRole::CondForm),
            (d3(0b111), CompilerLoweringRole::PairConstruct),
            (d4(0b0010), CompilerLoweringRole::LambdaForm),
            (d4(0b0011), CompilerLoweringRole::DefineForm),
        ];

        for (identity, expected_role) in expected {
            assert_eq!(
                compiler_lowering_role_from_sens(identity).expect("SENS role law"),
                Some(expected_role),
                "unexpected role for {identity:?}"
            );
        }

        assert_eq!(
            compiler_lowering_role_from_sens(d3(0b000)).expect("D3 empty"),
            None
        );
        assert_eq!(
            compiler_lowering_role_from_sens(d4(0b0111)).expect("D4 non-bootstrap"),
            None
        );
    }
}