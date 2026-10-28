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
    domain_identity_shape_or_empty_mechanism, eval_parsed_expressions, load_core_library,
    parse_mixed_exact_domain, sha256_source, CompilerExecutionRole, CompilerLoweringRole,
    CoreDomainIdentity, DomainIdentity, ErrorKind, Exactness, Expr, ExprKind, LanguageError,
    Session, Span, Value,
};
use std::rc::Rc;

const COMPILER_NUCLEUS_SOURCE: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const LANGUAGE_CONTRACT: &str = include_str!("../../../language-contract.lisp");

const LANGUAGE_CONTRACT_SHA256: &str = crate::binary_bootstrap::LANGUAGE_CONTRACT_SHA256;

pub const COMPILER_ROLE_LAW_REF: &str =
    "lib/compiler-nucleus.lisp:роль-пониження-компілятора-за-законами";
pub const COMPILER_D3_PROOF_REF: &str = "contracts/bija3-l1-l5-ratification.lisp";
pub const COMPILER_D4_PROOF_REF: &str = "contracts/d4-bootstrap-ratification.lisp";
pub const COMPILER_AUTHORITY_PATH: &str = "language-contract.lisp";
pub const COMPILER_CONTRACT_VERSION: &str = "12.0";
const D3_PROJECTION_SHA256: &str =
    "a93b29d70be2017c5e8088f51853d30c8c1efe42949aa74624416d3afea8f387";
const D4_PROJECTION_SHA256: &str =
    "bb4fc448038b897a48ed3f336c25a5581a56eaadbebc975a5fe4b43616b5af0b";

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

#[derive(Clone, Debug)]
pub struct CompilerProgramBootstrapBundle {
    pub d3_law: Value,
    pub d4_law: Value,
    pub d3_proof_ref: &'static str,
    pub d4_proof_ref: &'static str,
    pub request_provenance: Value,
    pub authority_path: &'static str,
    pub authority_sha256: String,
    pub language_contract_version: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerifiedCompilerProgramRequest {
    pub identity: CoreDomainIdentity,
    pub lowering_role: CompilerLoweringRole,
    pub proof_ref: String,
}

#[derive(Clone, Debug)]
pub struct VerifiedCompilerProgramArtifact {
    pub program_wire_sha256: String,
    pub sens_revision: String,
    pub authority_path: String,
    pub authority_sha256: String,
    pub language_contract_version: String,
    pub semantic_requests_sha256: String,
    pub semantic_requests: Value,
    pub requests: Vec<VerifiedCompilerProgramRequest>,
}
const LAW_PROJECTION: &str =
    include_str!("../../../knowledge/bija3-l1-l5-structure-projection.json");
const LAW_AUTHORITY: &str = include_str!("../../../contracts/bija3-l1-l5-ratification.lisp");
const LAW_AUTHORITY_SHA256: &str = crate::binary_bootstrap::BIJA3_L1_L5_RATIFICATION_SHA256;
const D4_LAW_PROJECTION: &str =
    include_str!("../../../knowledge/d4-bootstrap-compiler-structure-projection.json");
const D4_LAW_AUTHORITY: &str = include_str!("../../../contracts/d4-bootstrap-ratification.lisp");
const D4_LAW_AUTHORITY_SHA256: &str = crate::binary_bootstrap::D4_BOOTSTRAP_RATIFICATION_SHA256;

const SHAPE_MECHANISM_NAME: &str = "__compiler_domain_shape_mechanism";
const SHAPE_OR_EMPTY_MECHANISM_NAME: &str = "__compiler_domain_shape_or_empty_mechanism";
const PROGRAM_VALUE_NAME: &str = "__compiler_program_data";
const D3_PROOF_VALUE_NAME: &str = "__compiler_d3_proof";
const D4_PROOF_VALUE_NAME: &str = "__compiler_d4_proof";
const PROVENANCE_VALUE_NAME: &str = "__compiler_program_provenance";
const ARTIFACT_PROVENANCE_VALUE_NAME: &str = "__compiler_artifact_provenance";
const PROGRAM_DIGEST_VALUE_NAME: &str = "__compiler_program_wire_sha256";
const VALUE_DIGEST_MECHANISM_NAME: &str = "__compiler_canonical_value_sha256";
const LAW_VALUE_NAME: &str = "__compiler_l1_l5_law";
const D4_LAW_VALUE_NAME: &str = "__compiler_d4_bootstrap_law";

/// Exact SENS-owned inputs used by the compiler role law.
///
/// Callers that receive these assets through the Zig corridor can supply them
/// directly, keeping Rust from selecting or embedding project sources on that
/// execution path.
#[derive(Clone, Copy, Debug)]
pub struct CompilerLanguageSources<'a> {
    pub compiler_nucleus: &'a str,
    pub language_contract: &'a str,
    pub d3_projection: &'a str,
    pub d3_authority: &'a str,
    pub d4_projection: &'a str,
    pub d4_authority: &'a str,
}

impl CompilerLanguageSources<'static> {
    fn embedded() -> Self {
        Self {
            compiler_nucleus: COMPILER_NUCLEUS_SOURCE,
            language_contract: LANGUAGE_CONTRACT,
            d3_projection: LAW_PROJECTION,
            d3_authority: LAW_AUTHORITY,
            d4_projection: D4_LAW_PROJECTION,
            d4_authority: D4_LAW_AUTHORITY,
        }
    }
}

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
        return Err(invalid_projection(
            "generated law domain width is not numeric",
        ));
    }
    digits
        .parse()
        .map_err(|_| invalid_projection("generated law domain width is invalid"))
}

fn projection_string_array(source: &str, key: &str) -> Result<Vec<String>, LanguageError> {
    let marker = format!("\"{key}\": [");
    let start = source.find(&marker).ok_or_else(|| {
        invalid_projection(format!("generated law projection has no {key} array"))
    })? + marker.len();
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

fn projection_spine_from(source: &str) -> Result<Vec<String>, LanguageError> {
    let marker = "\"L5_spine\": [";
    let start = source
        .find(marker)
        .ok_or_else(|| invalid_projection("generated law projection has no L5 spine"))?
        + marker.len();
    let tail = &source[start..];
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

fn verify_compiler_sources(sources: &CompilerLanguageSources<'_>) -> Result<(), LanguageError> {
    for (name, bytes, expected) in [
        (
            "language contract",
            sources.language_contract.as_bytes(),
            LANGUAGE_CONTRACT_SHA256,
        ),
        (
            "D3 compiler projection",
            sources.d3_projection.as_bytes(),
            D3_PROJECTION_SHA256,
        ),
        (
            "D3 compiler authority",
            sources.d3_authority.as_bytes(),
            LAW_AUTHORITY_SHA256,
        ),
        (
            "D4 compiler projection",
            sources.d4_projection.as_bytes(),
            D4_PROJECTION_SHA256,
        ),
        (
            "D4 compiler authority",
            sources.d4_authority.as_bytes(),
            D4_LAW_AUTHORITY_SHA256,
        ),
    ] {
        if sha256_hex(bytes) != expected {
            return Err(invalid_projection(format!(
                "Zig-carried {name} asset has a stale or unexpected SHA-256"
            )));
        }
    }
    Ok(())
}

fn compiler_artifact_list<'a>(
    value: &'a Value,
    context: &str,
) -> Result<Vec<&'a Value>, LanguageError> {
    let mut items = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Nil => return Ok(items),
            Value::Pair(node) => {
                items.push(&node.head);
                cursor = &node.tail;
            }
            other => {
                return Err(invalid_projection(format!(
                    "{context} must be a proper list, got {other}"
                )));
            }
        }
    }
}

fn compiler_artifact_field<'a>(
    rows: &[&'a Value],
    field: &str,
) -> Result<&'a Value, LanguageError> {
    let mut found = None;
    for row in rows {
        let parts = compiler_artifact_list(row, "compiler artifact field")?;
        if parts.len() != 2 {
            return Err(invalid_projection(
                "compiler artifact fields must contain exactly name and value",
            ));
        }
        if compiler_surface_text(parts[0]).as_deref() == Some(field) {
            if found.is_some() {
                return Err(invalid_projection(format!(
                    "compiler artifact field {field} is duplicated"
                )));
            }
            found = Some(parts[1]);
        }
    }
    found.ok_or_else(|| invalid_projection(format!("compiler artifact field {field} is missing")))
}

fn compiler_artifact_string(value: &Value, field: &str) -> Result<String, LanguageError> {
    match value {
        Value::String(value) => Ok(value.to_string()),
        Value::Text7(value) => crate::text7_projection::render_text7(value, crate::Text7Layout::En)
            .map_err(|error| {
                invalid_projection(format!(
                    "compiler artifact field {field} contains unrenderable D7 text: {error}"
                ))
            }),
        other => Err(invalid_projection(format!(
            "compiler artifact field {field} must be a string, got {other}"
        ))),
    }
}

fn compiler_surface_text(value: &Value) -> Option<String> {
    match value {
        Value::Symbol(value) => Some(value.to_string()),
        Value::Text7(value) => {
            crate::text7_projection::render_text7(value, crate::Text7Layout::En).ok()
        }
        // Ядро компілятора СЕНС повертає цитований D7-текст як правильний список
        // точних D7-ідентичностей. Декодуємо його лише на цій межі;
        // не розширюємо ширину, не маскуємо біти й не тлумачимо інші типи як текст.
        Value::Pair(_) => {
            let mut cells = Vec::new();
            let mut cursor = value;
            loop {
                match cursor {
                    Value::Nil => break,
                    Value::Pair(node) => {
                        let Value::DomainIdentity(DomainIdentity::D7(cell)) = &node.head else {
                            return None;
                        };
                        cells.push(cell.word().packed_bits());
                        cursor = &node.tail;
                    }
                    _ => return None,
                }
            }
            let text = crate::Text7::from_cells(cells).ok()?;
            crate::text7_projection::render_text7(&text, crate::Text7Layout::En).ok()
        }
        _ => None,
    }
}

fn valid_lower_hex(value: &str, len: usize) -> bool {
    value.len() == len
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}

fn verify_compiler_program_request(
    request: &Value,
    role_session: &mut Session,
) -> Result<VerifiedCompilerProgramRequest, LanguageError> {
    let parts = compiler_artifact_list(request, "compiler semantic request")?;
    if parts.len() != 4 {
        return Err(invalid_projection(
            "compiler semantic request must contain identity, role, proof and provenance",
        ));
    }

    let Value::DomainIdentity(identity) = parts[0] else {
        return Err(invalid_projection(
            "compiler semantic request identity must be exact DomainIdentity",
        ));
    };
    let core = identity.core_operation().ok_or_else(|| {
        invalid_projection("compiler semantic request identity is not a callable Core identity")
    })?;
    let role = decode_language_lowering_role(parts[1])?
        .ok_or_else(|| invalid_projection("compiler semantic request role must not be empty"))?;
    let derived = eval_parsed_expressions(&[language_role_call(core)], role_session)?.value;
    let expected_role = decode_language_lowering_role(&derived)?
        .ok_or_else(|| invalid_projection("compiler semantic request identity has no SENS role"))?;
    if role != expected_role {
        return Err(invalid_projection(
            "compiler semantic request role disagrees with current SENS authority",
        ));
    }

    let proof_ref = compiler_artifact_string(parts[2], "semantic-request proof-ref")?;
    if proof_ref != proof_ref_for_lowering_role(role) {
        return Err(invalid_projection(
            "compiler semantic request proof disagrees with current SENS authority",
        ));
    }

    let provenance = compiler_artifact_list(parts[3], "semantic-request provenance")?;
    if provenance.len() != 3 {
        return Err(invalid_projection(
            "compiler semantic request provenance must contain path, authority digest and contract version",
        ));
    }
    let path = compiler_artifact_string(provenance[0], "semantic-request authority path")?;
    let authority_sha =
        compiler_artifact_string(provenance[1], "semantic-request authority digest")?;
    let contract_version =
        compiler_artifact_string(provenance[2], "semantic-request contract version")?;
    if path != COMPILER_AUTHORITY_PATH
        || authority_sha != LANGUAGE_CONTRACT_SHA256
        || contract_version != COMPILER_CONTRACT_VERSION
    {
        return Err(invalid_projection(
            "compiler semantic request provenance disagrees with current SENS authority",
        ));
    }

    Ok(VerifiedCompilerProgramRequest {
        identity: core,
        lowering_role: role,
        proof_ref,
    })
}

fn authority_sha256_from(projection: &str) -> Result<String, LanguageError> {
    let authority = projection.find("\"semantic_authority\"").ok_or_else(|| {
        invalid_projection("generated law projection has no authority provenance")
    })?;
    quoted_json_string(&projection[authority..], "sha256")
}

fn verify_projection_authority(projection: &str, authority: &str) -> Result<(), LanguageError> {
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

fn compiler_l1_l5_law_value_from(
    projection: &str,
    authority: &str,
) -> Result<Value, LanguageError> {
    if !projection.contains("\"status\": \"generated-projection-only\"") {
        return Err(invalid_projection(
            "compiler law input is not marked generated-projection-only",
        ));
    }
    if !projection.contains("\"compiler_role_table\": false") {
        return Err(invalid_projection(
            "generated law projection must forbid a compiler role table",
        ));
    }
    for forbidden in ["SelectorHead", "SelectorTail", "PairConstruct"] {
        if projection.contains(forbidden) {
            return Err(invalid_projection(format!(
                "generated structural law projection precomputes compiler role {forbidden}"
            )));
        }
    }

    verify_projection_authority(projection, authority)?;

    let width = projection_width_from(projection)?;
    let empty = quoted_json_string(projection, "L1_empty")?;
    let mask = quoted_json_string(projection, "L4_dual_xor_mask")?;
    let spine = projection_spine_from(projection)?;
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

fn compiler_l1_l5_law_value() -> Result<Value, LanguageError> {
    compiler_l1_l5_law_value_from(LAW_PROJECTION, LAW_AUTHORITY)
}

fn compiler_d4_bootstrap_law_value_from(
    projection: &str,
    authority: &str,
) -> Result<Value, LanguageError> {
    if !projection.contains("\"status\": \"generated-projection-only\"") {
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
        if !projection.contains(required_false) {
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
        if projection.contains(forbidden) {
            return Err(invalid_projection(format!(
                "D4 structural projection precomputes compiler role {forbidden}"
            )));
        }
    }

    verify_projection_authority(projection, authority)?;

    let width = projection_width_from(projection)?;
    if width != 4 {
        return Err(invalid_projection(format!(
            "D4 bootstrap projection must have exact width 4, got {width}"
        )));
    }

    let parent = quoted_json_string(projection, "parent_bits")?;
    if parent.len() + 1 != width {
        return Err(invalid_projection(
            "D4 bootstrap parent must be the exact one-bit-shorter fibre prefix",
        ));
    }

    let children = projection_string_array(projection, "children")?;
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

fn compiler_d4_bootstrap_law_value() -> Result<Value, LanguageError> {
    compiler_d4_bootstrap_law_value_from(D4_LAW_PROJECTION, D4_LAW_AUTHORITY)
}

/// Return the verified, representation-only bootstrap values required by the
/// compiled C1 whole-program entry.
///
/// This function does not expose or compute any DomainIdentity -> role mapping.
/// D3/D4 role meaning remains inside the SENS-written compiler nucleus. The
/// bundle contains only already-verified structural-law values, proof
/// references and language-authority provenance needed to install that nucleus
/// in another substrate. The executable nucleus itself travels as exact T5M
/// domain words; no host digest substitutes for that stream.
pub fn compiler_program_bootstrap_bundle() -> Result<CompilerProgramBootstrapBundle, LanguageError>
{
    let authority_sha256 = LANGUAGE_CONTRACT_SHA256.to_owned();
    Ok(CompilerProgramBootstrapBundle {
        d3_law: compiler_l1_l5_law_value()?,
        d4_law: compiler_d4_bootstrap_law_value()?,
        d3_proof_ref: COMPILER_D3_PROOF_REF,
        d4_proof_ref: COMPILER_D4_PROOF_REF,
        request_provenance: Value::list([
            Value::String(Rc::from(COMPILER_AUTHORITY_PATH)),
            Value::String(Rc::from(authority_sha256.as_str())),
            Value::String(Rc::from(COMPILER_CONTRACT_VERSION)),
        ]),
        authority_path: COMPILER_AUTHORITY_PATH,
        authority_sha256,
        language_contract_version: COMPILER_CONTRACT_VERSION,
    })
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
                symbol("роль-пониження-компілятора-за-законами"),
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
                symbol("скомпілювати-програму-компілятора"),
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

fn eval_compiler_nucleus_from(session: &mut Session, source: &str) -> Result<(), LanguageError> {
    let expressions = parse_mixed_exact_domain(source)?;
    eval_parsed_expressions(&expressions, session)?;
    Ok(())
}

fn eval_compiler_nucleus(session: &mut Session) -> Result<(), LanguageError> {
    crate::binary_bootstrap::compiler_nucleus_program()?.execute(session)?;
    Ok(())
}

fn compiler_program_artifact_call() -> Expr {
    Expr {
        kind: ExprKind::List(Rc::from(
            vec![
                symbol("скомпілювати-артефакт-програми-компілятора"),
                symbol(SHAPE_OR_EMPTY_MECHANISM_NAME),
                symbol(SHAPE_MECHANISM_NAME),
                symbol(VALUE_DIGEST_MECHANISM_NAME),
                symbol(PROGRAM_VALUE_NAME),
                symbol(LAW_VALUE_NAME),
                symbol(D4_LAW_VALUE_NAME),
                symbol(D3_PROOF_VALUE_NAME),
                symbol(D4_PROOF_VALUE_NAME),
                symbol(PROVENANCE_VALUE_NAME),
                symbol(ARTIFACT_PROVENANCE_VALUE_NAME),
                symbol(PROGRAM_DIGEST_VALUE_NAME),
            ]
            .into_boxed_slice(),
        )),
        span: Span::default(),
    }
}

fn decode_language_lowering_role(
    value: &Value,
) -> Result<Option<CompilerLoweringRole>, LanguageError> {
    // The source adapter historically surfaced role atoms as host Symbols;
    // physical T5M returns their canonical D7 Text7 datum. Normalize only at
    // this typed API boundary through D7's ratified ASCII projection.
    let name = match value {
        Value::Nil => return Ok(None),
        Value::Symbol(name) => name.to_string(),
        Value::Text7(text) => crate::text7_projection::render_text7(text, crate::Text7Layout::En)
            .map_err(|error| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                format!("SENS compiler nucleus returned unrenderable D7 role text: {error}"),
                Span::default(),
            )
        })?,
        // A source-written quoted D7 token can arrive as a proper list of
        // exact D7 identities. Normalize that representation here only; SENS
        // remains the authority that chose the role value.
        Value::Pair(_) => {
            let mut cells = Vec::new();
            let mut cursor = value;
            loop {
                match cursor {
                    Value::Nil => break,
                    Value::Pair(pair) => {
                        let Value::DomainIdentity(DomainIdentity::D7(cell)) = &pair.head else {
                            return Err(LanguageError::new(
                                ErrorKind::InvalidForm,
                                "SENS compiler nucleus returned a role list containing non-D7 data",
                                Span::default(),
                            ));
                        };
                        cells.push(cell.word().packed_bits());
                        cursor = &pair.tail;
                    }
                    other => {
                        return Err(LanguageError::new(
                            ErrorKind::InvalidForm,
                            format!(
                                "SENS compiler nucleus returned an improper D7 role list: {other}"
                            ),
                            Span::default(),
                        ));
                    }
                }
            }
            let text = crate::Text7::from_cells(cells).map_err(|_| {
                LanguageError::new(
                    ErrorKind::InvalidForm,
                    "SENS compiler nucleus returned malformed D7 role cells",
                    Span::default(),
                )
            })?;
            crate::text7_projection::render_text7(&text, crate::Text7Layout::En).map_err(
                |error| {
                    LanguageError::new(
                        ErrorKind::InvalidForm,
                        format!(
                            "SENS compiler nucleus returned unrenderable D7 role text: {error}"
                        ),
                        Span::default(),
                    )
                },
            )?
        }
        other => {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                format!("SENS compiler nucleus returned non-role value: {other}"),
                Span::default(),
            ));
        }
    };
    let role = match name.as_str() {
        "quote-form" => CompilerLoweringRole::QuoteForm,
        "atom-predicate" => CompilerLoweringRole::AtomPredicate,
        "selector-tail" => CompilerLoweringRole::SelectorTail,
        "selector-head" => CompilerLoweringRole::SelectorHead,
        "atom-equality" => CompilerLoweringRole::AtomEquality,
        "cond-form" => CompilerLoweringRole::CondForm,
        "pair-construct" => CompilerLoweringRole::PairConstruct,
        "lambda-form" => CompilerLoweringRole::LambdaForm,
        "define-form" => CompilerLoweringRole::DefineForm,
        _ => {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                format!("SENS compiler nucleus returned unknown abstract role: {name}"),
                Span::default(),
            ));
        }
    };
    Ok(Some(role))
}

/// Derive the complete current compiler lowering role by executing the
/// SENS-owned compiler law over the ratified D3 and D4 structural inputs.
pub fn compiler_lowering_role_from_sens(
    identity: CoreDomainIdentity,
) -> Result<Option<CompilerLoweringRole>, LanguageError> {
    compiler_lowering_role_from_sens_with_sources(identity, &CompilerLanguageSources::embedded())
}

fn compiler_lowering_role_from_sens_with_sources(
    identity: CoreDomainIdentity,
    sources: &CompilerLanguageSources<'_>,
) -> Result<Option<CompilerLoweringRole>, LanguageError> {
    verify_compiler_sources(sources)?;
    let mut session = Session::bare();
    load_core_library(&mut session)?;

    session
        .environment
        .define(SHAPE_MECHANISM_NAME, domain_identity_shape_mechanism());
    session.environment.define(
        LAW_VALUE_NAME,
        compiler_l1_l5_law_value_from(sources.d3_projection, sources.d3_authority)?,
    );
    session.environment.define(
        D4_LAW_VALUE_NAME,
        compiler_d4_bootstrap_law_value_from(sources.d4_projection, sources.d4_authority)?,
    );

    eval_compiler_nucleus_from(&mut session, sources.compiler_nucleus)?;

    let result = eval_parsed_expressions(&[language_role_call(identity)], &mut session)?.value;
    decode_language_lowering_role(&result)
}

fn install_compiler_program_bindings(
    session: &mut Session,
    program: Value,
) -> Result<(), LanguageError> {
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
            Value::String(Rc::from(LANGUAGE_CONTRACT_SHA256)),
            Value::String(Rc::from(COMPILER_CONTRACT_VERSION)),
        ]),
    );
    Ok(())
}

/// Execute the SENS-written recursive compiler traversal over canonical
/// program-data.  The host adapter supplies representation mechanisms and
/// provenance values once; it does not walk nodes or select compiler roles.
///
/// Return shape is owned by `lib/compiler-nucleus.lisp`:
/// `(D1-success-bit request...)`.
pub fn compiler_program_requests_from_sens(program: Value) -> Result<Value, LanguageError> {
    let mut session = Session::bare();
    load_core_library(&mut session)?;
    install_compiler_program_bindings(&mut session, program)?;
    eval_compiler_nucleus(&mut session)?;
    Ok(eval_parsed_expressions(&[compiler_program_call()], &mut session)?.value)
}

/// Compose one backend-neutral whole-program artifact inside SENS.
///
/// `program_wire_sha256` is mechanical transport provenance for the exact
/// canonical SW\\x01 bytes.  The host does not choose, iterate or serialize
/// semantic requests; SENS performs traversal and artifact composition in one
/// call.
pub fn compiler_program_artifact_from_sens(
    program: Value,
    program_wire_sha256: &str,
    sens_revision: &str,
) -> Result<Value, LanguageError> {
    if program_wire_sha256.len() != 64
        || !program_wire_sha256
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        return Err(invalid_projection(
            "compiler program wire digest must be exactly 64 lowercase hexadecimal characters",
        ));
    }
    if sens_revision.len() != 40
        || !sens_revision
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        return Err(invalid_projection(
            "compiler SENS revision must be exactly 40 lowercase hexadecimal characters",
        ));
    }

    let mut session = Session::bare();
    load_core_library(&mut session)?;
    install_compiler_program_bindings(&mut session, program)?;
    session.environment.define(
        VALUE_DIGEST_MECHANISM_NAME,
        canonical_value_sha256_mechanism(),
    );
    session.environment.define(
        PROGRAM_DIGEST_VALUE_NAME,
        Value::String(Rc::from(program_wire_sha256)),
    );
    session.environment.define(
        ARTIFACT_PROVENANCE_VALUE_NAME,
        Value::list([
            Value::String(Rc::from(sens_revision)),
            Value::String(Rc::from(COMPILER_AUTHORITY_PATH)),
            Value::String(Rc::from(LANGUAGE_CONTRACT_SHA256)),
            Value::String(Rc::from(COMPILER_CONTRACT_VERSION)),
        ]),
    );
    eval_compiler_nucleus(&mut session)?;
    Ok(eval_parsed_expressions(&[compiler_program_artifact_call()], &mut session)?.value)
}

/// Verify a decoded SENS whole-program compiler artifact before any backend
/// mechanism binds to it.
///
/// The expected wire digest and SENS revision are supplied by the caller as
/// transport provenance. Schema, authority, request digest, role, proof and
/// request provenance are all checked against current SENS-owned authority.
pub fn verify_compiler_program_artifact_from_sens(
    artifact: &Value,
    expected_program_wire_sha256: &str,
    expected_sens_revision: &str,
) -> Result<VerifiedCompilerProgramArtifact, LanguageError> {
    if !valid_lower_hex(expected_program_wire_sha256, 64) {
        return Err(invalid_projection(
            "expected compiler program wire digest must be exactly 64 lowercase hexadecimal characters",
        ));
    }
    if !valid_lower_hex(expected_sens_revision, 40) {
        return Err(invalid_projection(
            "expected compiler SENS revision must be exactly 40 lowercase hexadecimal characters",
        ));
    }

    let rows = compiler_artifact_list(artifact, "compiler program artifact")?;
    let Some(schema) = rows.first().and_then(|value| compiler_surface_text(value)) else {
        return Err(invalid_projection(
            "compiler program artifact must start with a D7 text schema name",
        ));
    };
    if schema == "compiler-compilation-error-1" {
        return Err(invalid_projection(
            "compiler-compilation-error-1 cannot enter executable lowering",
        ));
    }
    if schema != "compiler-compilation-artifact-1" {
        return Err(invalid_projection(format!(
            "unknown compiler program artifact schema: {schema}"
        )));
    }

    const ALLOWED_FIELDS: [&str; 7] = [
        "artifact-kind",
        "program-wire-sha256",
        "semantic-requests-sha256",
        "authority-provenance",
        "semantic-requests",
        "required-capabilities",
        "artifact-status",
    ];
    // Exactly seven transport/schema slots: position is a local mask bit,
    // never a numeric SENS-domain identity or a re-interpretation of W1–W10.
    let mut seen_fields = 0u8;
    for row in &rows[1..] {
        let parts = compiler_artifact_list(row, "compiler artifact field")?;
        if parts.len() != 2 {
            return Err(invalid_projection(
                "compiler artifact fields must contain exactly name and value",
            ));
        }
        let name = compiler_surface_text(parts[0])
            .ok_or_else(|| invalid_projection("compiler artifact field name must be D7 text"))?;
        let Some(index) = ALLOWED_FIELDS.iter().position(|&allowed| allowed == name) else {
            return Err(invalid_projection(format!(
                "compiler artifact contains unsupported field {name}"
            )));
        };
        let bit = 1u8 << index;
        if seen_fields & bit != 0 {
            return Err(invalid_projection(format!(
                "duplicate compiler artifact field {name}"
            )));
        }
        seen_fields |= bit;
    }

    let kind = compiler_artifact_field(&rows[1..], "artifact-kind")?;
    if compiler_surface_text(kind).as_deref() != Some("whole-program") {
        return Err(invalid_projection(
            "compiler artifact kind must be whole-program",
        ));
    }
    let status = compiler_artifact_field(&rows[1..], "artifact-status")?;
    if compiler_surface_text(status).as_deref() != Some("canonical-backend-neutral") {
        return Err(invalid_projection(
            "compiler artifact status must be canonical-backend-neutral",
        ));
    }
    if !matches!(
        compiler_artifact_field(&rows[1..], "required-capabilities")?,
        Value::Nil
    ) {
        return Err(invalid_projection(
            "compiler artifact required-capabilities must be empty",
        ));
    }

    let program_wire_sha256 = compiler_artifact_string(
        compiler_artifact_field(&rows[1..], "program-wire-sha256")?,
        "program-wire-sha256",
    )?;
    if program_wire_sha256 != expected_program_wire_sha256 {
        return Err(invalid_projection(
            "compiler artifact program wire digest does not match caller provenance",
        ));
    }

    let provenance = compiler_artifact_list(
        compiler_artifact_field(&rows[1..], "authority-provenance")?,
        "compiler artifact authority provenance",
    )?;
    if provenance.len() != 4 {
        return Err(invalid_projection(
            "compiler artifact authority provenance must contain revision, path, authority digest and contract version",
        ));
    }
    let sens_revision = compiler_artifact_string(provenance[0], "SENS revision")?;
    let authority_path = compiler_artifact_string(provenance[1], "authority path")?;
    let authority_sha256 = compiler_artifact_string(provenance[2], "authority digest")?;
    let language_contract_version =
        compiler_artifact_string(provenance[3], "language contract version")?;
    if sens_revision != expected_sens_revision
        || authority_path != COMPILER_AUTHORITY_PATH
        || authority_sha256 != LANGUAGE_CONTRACT_SHA256
        || language_contract_version != COMPILER_CONTRACT_VERSION
    {
        return Err(invalid_projection(
            "compiler artifact authority provenance disagrees with current SENS authority",
        ));
    }

    let semantic_requests = compiler_artifact_field(&rows[1..], "semantic-requests")?.clone();
    let requests = compiler_artifact_list(&semantic_requests, "compiler semantic requests")?;
    if requests.is_empty() {
        return Err(invalid_projection(
            "compiler whole-program artifact must contain semantic requests",
        ));
    }
    let semantic_requests_sha256 = compiler_artifact_string(
        compiler_artifact_field(&rows[1..], "semantic-requests-sha256")?,
        "semantic-requests-sha256",
    )?;
    let canonical_requests =
        crate::compiler_evidence_canonical_bytes(&semantic_requests).map_err(invalid_projection)?;
    if sha256_hex(&canonical_requests) != semantic_requests_sha256 {
        return Err(invalid_projection(
            "compiler artifact semantic request digest mismatch",
        ));
    }

    let mut role_session = Session::bare();
    load_core_library(&mut role_session)?;
    role_session
        .environment
        .define(SHAPE_MECHANISM_NAME, domain_identity_shape_mechanism());
    role_session
        .environment
        .define(LAW_VALUE_NAME, compiler_l1_l5_law_value()?);
    role_session
        .environment
        .define(D4_LAW_VALUE_NAME, compiler_d4_bootstrap_law_value()?);
    eval_compiler_nucleus(&mut role_session)?;

    let verified_requests = requests
        .into_iter()
        .map(|request| verify_compiler_program_request(request, &mut role_session))
        .collect::<Result<Vec<_>, _>>()?;

    Ok(VerifiedCompilerProgramArtifact {
        program_wire_sha256,
        sens_revision,
        authority_path,
        authority_sha256,
        language_contract_version,
        semantic_requests_sha256,
        semantic_requests,
        requests: verified_requests,
    })
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
fn proof_ref_for_lowering_role(role: CompilerLoweringRole) -> &'static str {
    match role {
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
    }
}

pub fn compiler_semantic_input_from_sens(
    identity: CoreDomainIdentity,
) -> Result<Option<CompilerSemanticInput>, LanguageError> {
    compiler_semantic_input_from_sens_with_sources(identity, &CompilerLanguageSources::embedded())
}

/// Derive a compiler role using source bytes supplied by the Zig transport.
/// SENS still parses and evaluates every law; the supplied assets are checked
/// against their ratified authority before the role can be returned.
pub fn compiler_semantic_input_from_sens_with_sources(
    identity: CoreDomainIdentity,
    sources: &CompilerLanguageSources<'_>,
) -> Result<Option<CompilerSemanticInput>, LanguageError> {
    let Some(lowering_role) = compiler_lowering_role_from_sens_with_sources(identity, sources)?
    else {
        return Ok(None);
    };

    let proof_ref = proof_ref_for_lowering_role(lowering_role);

    Ok(Some(CompilerSemanticInput {
        identity,
        lowering_role,
        authority_ref: COMPILER_ROLE_LAW_REF,
        proof_ref,
        semantic_status: "current",
        authority_path: COMPILER_AUTHORITY_PATH,
        authority_sha256: sha256_hex(sources.language_contract.as_bytes()),
        language_contract_version: COMPILER_CONTRACT_VERSION,
    }))
}

pub fn compiler_execution_role_from_sens(
    identity: CoreDomainIdentity,
) -> Result<Option<CompilerExecutionRole>, LanguageError> {
    match compiler_lowering_role_from_sens(identity)? {
        Some(CompilerLoweringRole::SelectorHead) => Ok(Some(CompilerExecutionRole::SelectorHead)),
        Some(CompilerLoweringRole::SelectorTail) => Ok(Some(CompilerExecutionRole::SelectorTail)),
        Some(CompilerLoweringRole::PairConstruct) => Ok(Some(CompilerExecutionRole::PairConstruct)),
        Some(_) | None => Ok(None),
    }
}

