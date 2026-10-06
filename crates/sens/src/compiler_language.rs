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
    canonical_value_sha256_mechanism, domain_identity_shape_mechanism,
    domain_identity_shape_or_empty_mechanism, eval_parsed_expressions, eval_program,
    load_core_library,
    sha256_source, CompilerExecutionRole, CompilerLoweringRole, CoreDomainIdentity, DomainIdentity,
    ErrorKind, Exactness,
    Expr, ExprKind, LanguageError, Session, Span, Value,
};
use std::rc::Rc;

const COMPILER_NUCLEUS_SOURCE: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const LANGUAGE_CONTRACT: &str = include_str!("../../../language-contract.lisp");
const COMPILATION_ARTIFACT_V2_CONTRACT: &str =
    include_str!("../../../contracts/compiler-compilation-artifact-v2.lisp");

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
const SHAPE_OR_EMPTY_MECHANISM_NAME: &str = "__compiler_domain_shape_or_empty_mechanism";
const PROGRAM_VALUE_NAME: &str = "__compiler_program_data";
const D3_PROOF_VALUE_NAME: &str = "__compiler_d3_proof";
const D4_PROOF_VALUE_NAME: &str = "__compiler_d4_proof";
const PROVENANCE_VALUE_NAME: &str = "__compiler_program_provenance";
const DIGEST_MECHANISM_NAME: &str = "__compiler_canonical_value_sha256_mechanism";
const LAW_VALUE_NAME: &str = "__compiler_l1_l5_law";
const D4_LAW_VALUE_NAME: &str = "__compiler_d4_bootstrap_law";

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

fn compiler_program_call() -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(
            vec![
                symbol("compiler-compile-program"),
                symbol(SHAPE_OR_EMPTY_MECHANISM_NAME),
                symbol(SHAPE_MECHANISM_NAME),
                symbol(PROGRAM_VALUE_NAME),
                symbol(LAW_VALUE_NAME),
                symbol(D4_LAW_VALUE_NAME),
                symbol(D3_PROOF_VALUE_NAME),
                symbol(D4_PROOF_VALUE_NAME),
                symbol(PROVENANCE_VALUE_NAME),
            ]
            .into_boxed_slice(),
        )),
        span: Span::default(),
    }
}


fn compiler_program_artifact_call() -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(
            vec![
                symbol("compiler-compile-program-artifact"),
                symbol(SHAPE_OR_EMPTY_MECHANISM_NAME),
                symbol(SHAPE_MECHANISM_NAME),
                symbol(DIGEST_MECHANISM_NAME),
                symbol(PROGRAM_VALUE_NAME),
                symbol(LAW_VALUE_NAME),
                symbol(D4_LAW_VALUE_NAME),
                symbol(D3_PROOF_VALUE_NAME),
                symbol(D4_PROOF_VALUE_NAME),
                symbol(PROVENANCE_VALUE_NAME),
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

/// Execute the SENS-written recursive compiler traversal over canonical
/// program-data.  The host adapter supplies representation mechanisms and
/// provenance values once; it does not walk nodes or select compiler roles.
///
/// Return shape is owned by `lib/compiler-nucleus.lisp`:
/// `(D1-success-bit request...)`.
pub fn compiler_program_requests_from_sens(program: Value) -> Result<Value, LanguageError> {
    let mut session = Session::default();
    load_core_library(&mut session)?;

    session
        .environment
        .define(SHAPE_MECHANISM_NAME, domain_identity_shape_mechanism());
    session.environment.define(
        SHAPE_OR_EMPTY_MECHANISM_NAME,
        domain_identity_shape_or_empty_mechanism(),
    );
    session
        .environment
        .define(LAW_VALUE_NAME, compiler_l1_l5_law_value()?);
    session
        .environment
        .define(D4_LAW_VALUE_NAME, compiler_d4_bootstrap_law_value()?);
    session.environment.define(PROGRAM_VALUE_NAME, program);
    session.environment.define(
        D3_PROOF_VALUE_NAME,
        Value::String(Rc::from(COMPILER_D3_PROOF_REF)),
    );
    session.environment.define(
        D4_PROOF_VALUE_NAME,
        Value::String(Rc::from(COMPILER_D4_PROOF_REF)),
    );
    session.environment.define(
        PROVENANCE_VALUE_NAME,
        Value::list([
            Value::String(Rc::from(COMPILER_AUTHORITY_PATH)),
            Value::String(Rc::from(sha256_hex(LANGUAGE_CONTRACT.as_bytes()))),
            Value::String(Rc::from(COMPILER_CONTRACT_VERSION)),
        ]),
    );

    eval_program(COMPILER_NUCLEUS_SOURCE, &mut session)?;
    Ok(eval_parsed_expressions(&[compiler_program_call()], &mut session)?.value)
}

fn canonical_revision(value: &str) -> Result<&str, LanguageError> {
    if value.len() == 40
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        Ok(value)
    } else {
        Err(invalid_projection(
            "SENS revision provenance must be exactly 40 lowercase hexadecimal characters",
        ))
    }
}

fn compiler_program_provenance(sens_revision: &str) -> Result<Value, LanguageError> {
    let revision = canonical_revision(sens_revision)?;
    Ok(Value::list([
        Value::String(Rc::from(revision)),
        Value::String(Rc::from(COMPILER_AUTHORITY_PATH)),
        Value::String(Rc::from(sha256_hex(LANGUAGE_CONTRACT.as_bytes()))),
        Value::String(Rc::from(COMPILER_CONTRACT_VERSION)),
        Value::String(Rc::from(sha256_hex(COMPILER_NUCLEUS_SOURCE.as_bytes()))),
    ]))
}

/// Bootstrap parity witness for the SENS-owned whole-program compilation
/// artifact.  This adapter installs only representation mechanisms and opaque
/// provenance.  Traversal, request selection, digest selection and artifact
/// composition execute inside `lib/compiler-nucleus.lisp`.
///
/// Executable C1 must expose the same SENS operation through #3840/#630 rather
/// than calling this Rust helper.
pub fn compiler_program_artifact_from_sens(
    program: Value,
    sens_revision: &str,
) -> Result<Value, LanguageError> {
    if !COMPILATION_ARTIFACT_V2_CONTRACT
        .contains("(schema . compiler-compilation-artifact/2)")
    {
        return Err(invalid_projection(
            "whole-program compilation artifact v2 contract is missing its schema",
        ));
    }

    let mut session = Session::default();
    load_core_library(&mut session)?;

    session
        .environment
        .define(SHAPE_MECHANISM_NAME, domain_identity_shape_mechanism());
    session.environment.define(
        SHAPE_OR_EMPTY_MECHANISM_NAME,
        domain_identity_shape_or_empty_mechanism(),
    );
    session
        .environment
        .define(DIGEST_MECHANISM_NAME, canonical_value_sha256_mechanism());
    session
        .environment
        .define(LAW_VALUE_NAME, compiler_l1_l5_law_value()?);
    session
        .environment
        .define(D4_LAW_VALUE_NAME, compiler_d4_bootstrap_law_value()?);
    session.environment.define(PROGRAM_VALUE_NAME, program);
    session.environment.define(
        D3_PROOF_VALUE_NAME,
        Value::String(Rc::from(COMPILER_D3_PROOF_REF)),
    );
    session.environment.define(
        D4_PROOF_VALUE_NAME,
        Value::String(Rc::from(COMPILER_D4_PROOF_REF)),
    );
    session.environment.define(
        PROVENANCE_VALUE_NAME,
        compiler_program_provenance(sens_revision)?,
    );

    eval_program(COMPILER_NUCLEUS_SOURCE, &mut session)?;
    Ok(eval_parsed_expressions(&[compiler_program_artifact_call()], &mut session)?.value)
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

    fn list_values(value: &Value) -> Vec<&Value> {
        let mut out = Vec::new();
        let mut cursor = value;
        loop {
            match cursor {
                Value::Nil => return out,
                Value::Pair(head, tail) => {
                    out.push(head.as_ref());
                    cursor = tail.as_ref();
                }
                other => panic!("expected proper list, got {other}"),
            }
        }
    }

    fn exact_value(identity: CoreDomainIdentity) -> Value {
        Value::DomainIdentity(DomainIdentity::from_source_word(identity.source_word()))
    }

    #[test]
    fn sens_program_traversal_is_role_aware_and_quote_shields_domain_data() {
        let lambda = exact_value(d4(0b0010));
        let quote = exact_value(d3(0b001));
        let atom = exact_value(d3(0b010));
        let d8 = CoreDomainIdentity::D8(crate::CoreD8::from_word(
            crate::Bit8::new(0b0000_0010).expect("D8 word"),
        ));

        let program = Value::list([Value::list([
            lambda,
            Value::list([Value::Symbol(Rc::from("x"))]),
            Value::list([quote, exact_value(d8)]),
            Value::list([atom, Value::Symbol(Rc::from("x"))]),
        ])]);

        let result = compiler_program_requests_from_sens(program).expect("SENS program traversal");
        let rows = list_values(&result);
        assert_eq!(
            rows[0].as_predicate_bit(),
            Some(true),
            "quoted D8 data must not be traversed as a compiler call"
        );
        assert_eq!(rows.len(), 4, "success bit plus Lambda/Quote/Atom requests");

        let observed_roles = rows[1..]
            .iter()
            .map(|request| {
                let request = list_values(request);
                match request[1] {
                    Value::Symbol(role) => role.to_string(),
                    other => panic!("request role must be symbolic, got {other}"),
                }
            })
            .collect::<Vec<_>>();
        assert_eq!(observed_roles, ["lambda-form", "quote-form", "atom-predicate"]);
    }

    #[test]
    fn same_payload_wrong_domain_with_wrong_shape_fails_closed() {
        // D3:010 is AtomPredicate and one argument is valid.
        let d3_program = Value::list([Value::list([
            exact_value(d3(0b010)),
            Value::Symbol(Rc::from("x")),
        ])]);
        let d3_result =
            compiler_program_requests_from_sens(d3_program).expect("D3 atom traversal");
        let d3_rows = list_values(&d3_result);
        assert_eq!(d3_rows[0].as_predicate_bit(), Some(true));

        // Same numeric payload under width 4 is D4:0010 LambdaForm.
        // Reusing the one-child D3 source shape must fail rather than silently
        // reinterpret the node as a valid lambda request.
        let d4_program = Value::list([Value::list([
            exact_value(d4(0b0010)),
            Value::Symbol(Rc::from("x")),
        ])]);
        let d4_result =
            compiler_program_requests_from_sens(d4_program).expect("normal fail-closed result");
        let d4_rows = list_values(&d4_result);
        assert_eq!(d4_rows.len(), 1);
        assert_eq!(d4_rows[0].as_predicate_bit(), Some(false));
    }

    #[test]
    fn malformed_exact_d3_cond_clause_fails_closed_before_request_emission() {
        let cond = exact_value(d3(0b110));
        let malformed_clause = Value::list([Value::Symbol(Rc::from("test-only"))]);
        let program = Value::list([Value::list([cond, malformed_clause])]);

        let result =
            compiler_program_requests_from_sens(program).expect("normal fail-closed result");
        let rows = list_values(&result);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].as_predicate_bit(), Some(false));
    }

    #[test]
    fn direct_d8_domain_call_fails_closed_in_sens_program_traversal() {
        let d8 = CoreDomainIdentity::D8(crate::CoreD8::from_word(
            crate::Bit8::new(0b0000_0010).expect("D8 word"),
        ));
        let program = Value::list([Value::list([exact_value(d8)])]);

        let result = compiler_program_requests_from_sens(program).expect("normal fail-closed result");
        let rows = list_values(&result);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].as_predicate_bit(), Some(false));
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