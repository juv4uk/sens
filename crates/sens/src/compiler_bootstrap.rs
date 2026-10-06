//! Bootstrap-only mechanical view of exact domain identity.
//!
//! This module deliberately exposes representation, not SENS meaning.
//! It must never map a coordinate to CAR/CDR/CONS, a compiler role, or a
//! backend mechanism.  The returned function value is opt-in: embedders pass
//! it to SENS code explicitly while #3808/#3809 move compiler-law execution
//! into the language itself.

use crate::{sha256_source, ErrorKind, Exactness, LanguageError, Value};
use std::rc::Rc;

/// Build an opt-in mechanism value that decomposes one exact DomainIdentity.
///
/// Result:
///
///     (width (bit0 bit1 ... bitN))
///
/// Bits are exact D1 PredicateBit values in source order (MSB first).
/// Width is a host numeric representation fact, not a semantic-domain role.
///
/// This function does not register a global surface or mint a SENS identity.
pub fn domain_identity_shape_mechanism() -> Value {
    Value::host_function(Rc::new(|arguments, _environment, span| {
        if arguments.len() != 1 {
            return Err(LanguageError::new(
                ErrorKind::Arity,
                format!(
                    "domain identity shape mechanism expects exactly 1 argument, got {}",
                    arguments.len()
                ),
                span,
            ));
        }

        let identity = arguments[0].as_domain_identity().ok_or_else(|| {
            LanguageError::new(
                ErrorKind::Type,
                "domain identity shape mechanism expects an exact DomainIdentity",
                span,
            )
        })?;

        let width = identity.width();
        let packed = identity.packed_bits();

        let bits = (0..width).map(|index| {
            let shift = width - 1 - index;
            Value::predicate_bit(((packed >> shift) & 1) == 1)
        });

        Ok(Value::list([
            Value::Number(width as f64, Exactness::Exact),
            Value::list(bits),
        ]))
    }))
}

/// Build an opt-in representation predicate/decomposer for compiler program-data.
///
/// For an exact DomainIdentity this returns the same `(width bits)` shape as
/// `domain_identity_shape_mechanism`. Every other value returns NIL instead
/// of raising a type error. This is intentionally representation-only: it
/// does not admit a domain, choose a compiler role, select proof, or choose a
/// backend mechanism.
pub fn domain_identity_shape_or_empty_mechanism() -> Value {
    Value::host_function(Rc::new(|arguments, _environment, span| {
        if arguments.len() != 1 {
            return Err(LanguageError::new(
                ErrorKind::Arity,
                format!(
                    "domain identity shape-or-empty mechanism expects exactly 1 argument, got {}",
                    arguments.len()
                ),
                span,
            ));
        }

        let Some(identity) = arguments[0].as_domain_identity() else {
            return Ok(Value::Nil);
        };

        let width = identity.width();
        let packed = identity.packed_bits();
        let bits = (0..width).map(|index| {
            let shift = width - 1 - index;
            Value::predicate_bit(((packed >> shift) & 1) == 1)
        });

        Ok(Value::list([
            Value::Number(width as f64, Exactness::Exact),
            Value::list(bits),
        ]))
    }))
}

fn put_canonical_len(out: &mut Vec<u8>, len: usize) {
    out.extend_from_slice(&(len as u64).to_le_bytes());
}

fn encode_canonical_compiler_value(value: &Value, out: &mut Vec<u8>) -> Result<(), String> {
    match value {
        Value::Nil => out.push(0x00),
        Value::DomainIdentity(identity) => {
            out.push(0x01);
            out.push(identity.width() as u8);
            out.push(identity.packed_bits());
        }
        Value::Symbol(symbol) => {
            out.push(0x02);
            put_canonical_len(out, symbol.len());
            out.extend_from_slice(symbol.as_bytes());
        }
        Value::String(text) => {
            out.push(0x03);
            put_canonical_len(out, text.len());
            out.extend_from_slice(text.as_bytes());
        }
        Value::Pair(head, tail) => {
            out.push(0x04);
            encode_canonical_compiler_value(head, out)?;
            encode_canonical_compiler_value(tail, out)?;
        }
        other => {
            return Err(format!(
                "canonical compiler-value hash does not admit runtime value: {other}"
            ));
        }
    }
    Ok(())
}

/// Narrow representation-only SHA-256 capability for compiler evidence values.
///
/// The accepted value language is deliberately closed: NIL, exact
/// DomainIdentity, Symbol, String and Pair.  These are sufficient for the
/// proof-carrying compiler request sequence.  The mechanism has no knowledge
/// of compiler roles, laws, proof ownership or backend mechanisms.
pub fn canonical_compiler_value_sha256_mechanism() -> Value {
    Value::host_function(Rc::new(|arguments, _environment, span| {
        if arguments.len() != 1 {
            return Err(LanguageError::new(
                ErrorKind::Arity,
                format!(
                    "canonical compiler-value sha256 expects exactly 1 argument, got {}",
                    arguments.len()
                ),
                span,
            ));
        }

        let mut encoded = Vec::new();
        encode_canonical_compiler_value(&arguments[0], &mut encoded).map_err(|message| {
            LanguageError::new(ErrorKind::Type, message, span)
        })?;
        let digest = sha256_source(&encoded);
        let hex = digest.iter().map(|byte| format!("{byte:02x}")).collect::<String>();
        Ok(Value::String(Rc::from(hex)))
    }))
}
