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
    domain_identity_shape_mechanism, eval_parsed_expressions, eval_program, load_core_library,
    sha256_source, CompilerExecutionRole, CompilerLoweringRole, CoreDomainIdentity, DomainIdentity,
    ErrorKind, Exactness,
    Expr, ExprKind, LanguageError, Session, Span, Value,
};
use std::rc::Rc;

const COMPILER_NUCLEUS_SOURCE: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const LAW_PROJECTION: &str =
    include_str!("../../../knowledge/bija3-l1-l5-structure-projection.json");
const LAW_AUTHORITY: &str = include_str!("../../../contracts/bija3-l1-l5-ratification.lisp");
const D4_LAW_PROJECTION: &str =
    include_str!("../../../knowledge/d4-bootstrap-compiler-structure-projection.json");
const D4_LAW_AUTHORITY: &str = include_str!("../../../contracts/d4-bootstrap-ratification.lisp");

const SHAPE_MECHANISM_NAME: &str = "__compiler_domain_shape_mechanism";
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
                symbol("compiler-role-from-l1-l5"),
                symbol(SHAPE_MECHANISM_NAME),
                Expr {
                    kind: ExprKind::DomainIdentity(exact_identity),
                    span: Span::default(),
                },
                symbol(LAW_VALUE_NAME),
            ]
            .into_boxed_slice(),
        )),
        span: Span::default(),
    }
}

fn language_lowering_role_call(identity: CoreDomainIdentity) -> Expr {
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

fn decode_lowering_role(value: &Value) -> Result<Option<CompilerLoweringRole>, LanguageError> {
    let role = match value {
        Value::Nil => return Ok(None),
        Value::Symbol(name) => match name.as_ref() {
            "quote-form" => CompilerLoweringRole::QuoteForm,
            "atom-predicate" => CompilerLoweringRole::AtomPredicate,
            "selector-tail" => CompilerLoweringRole::SelectorTail,
            "selector-head" => CompilerLoweringRole::SelectorHead,
            "atom-equality" => CompilerLoweringRole::AtomEquality,
            "cond-form" => CompilerLoweringRole::CondForm,
            "pair-construct" => CompilerLoweringRole::PairConstruct,
            "lambda-form" => CompilerLoweringRole::LambdaForm,
            "define-form" => CompilerLoweringRole::DefineForm,
            other => {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("SENS compiler nucleus returned unknown lowering role: {other}"),
                    Span::default(),
                ))
            }
        },
        other => {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                format!("SENS compiler nucleus returned non-role value: {other}"),
                Span::default(),
            ))
        }
    };
    Ok(Some(role))
}

fn decode_language_role(value: &Value) -> Result<Option<CompilerExecutionRole>, LanguageError> {
    match value {
        Value::Nil => Ok(None),
        Value::Symbol(name) if name.as_ref() == "selector-head" => {
            Ok(Some(CompilerExecutionRole::SelectorHead))
        }
        Value::Symbol(name) if name.as_ref() == "selector-tail" => {
            Ok(Some(CompilerExecutionRole::SelectorTail))
        }
        Value::Symbol(name) if name.as_ref() == "pair-construct" => {
            Ok(Some(CompilerExecutionRole::PairConstruct))
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

/// Derive the bounded compiler role by executing the SENS-owned compiler law.
///
/// Rust does not inspect domain coordinates here. The older
/// `compiler_execution_role` function remains available as a differential
/// oracle while consumers migrate, but production compiler callers should use
/// this function.
pub fn compiler_execution_role_from_sens(
    identity: CoreDomainIdentity,
) -> Result<Option<CompilerExecutionRole>, LanguageError> {
    let mut session = Session::default();
    load_core_library(&mut session)?;

    session
        .environment
        .define(SHAPE_MECHANISM_NAME, domain_identity_shape_mechanism());
    session
        .environment
        .define(LAW_VALUE_NAME, compiler_l1_l5_law_value()?);

    eval_program(COMPILER_NUCLEUS_SOURCE, &mut session)?;

    let result = eval_parsed_expressions(&[language_role_call(identity)], &mut session)?.value;
    decode_language_role(&result)
}


/// Derive the complete current compiler-nucleus lowering role by executing
/// SENS-owned structural laws.  Rust transports the provenance-bound D3/D4
/// projections and decodes the returned abstract symbol; it never selects
/// meaning from raw domain coordinates.
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

    let result =
        eval_parsed_expressions(&[language_lowering_role_call(identity)], &mut session)?.value;
    decode_lowering_role(&result)
}


#[cfg(test)]
mod tests {
    use super::*;

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
}
