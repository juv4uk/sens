//! Explicit compatibility/backend bridge for historical exact-eight mechanisms.
//!
//! This module is intentionally domain-agnostic. Canonical domain code may
//! select an optional legacy mechanism coordinate, but only this compatibility
//! boundary materializes that coordinate as `Sens8`.
//!
//! No reverse edge exists here: a legacy byte/Sens8 never creates canonical
//! language identity.

use super::canon;
use crate::{Environment, LanguageError, Sens8, Span, Value};

pub(crate) fn invoke_legacy_mechanism_byte(
    byte: u8,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    canon::invoke_semantic_ref(
        Sens8::from_packed_byte(byte),
        args,
        environment,
        span,
    )
}

pub(crate) fn bind_legacy_mechanism_alias_once(
    byte: u8,
    value: &Value,
    environment: &Environment,
) {
    let sid = Sens8::from_packed_byte(byte);
    if !canon::has_primitive(sid) {
        environment.bind_code_slot_once(sid, value.clone());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn legacy_boundary_materializes_only_the_requested_exact_eight_coordinate() {
        let sid = Sens8::from_packed_byte(0b0000_1100);
        assert_eq!(sid.packed_byte(), 0b0000_1100);
    }
}
