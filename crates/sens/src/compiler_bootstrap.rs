//! Bootstrap-only mechanical view of exact domain identity.
//!
//! This module deliberately exposes representation, not SENS meaning.
//! It must never map a coordinate to CAR/CDR/CONS, a compiler role, or a
//! backend mechanism.  The returned function value is opt-in: embedders pass
//! it to SENS code explicitly while #3808/#3809 move compiler-law execution
//! into the language itself.

use crate::{ErrorKind, Exactness, LanguageError, Value};
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
