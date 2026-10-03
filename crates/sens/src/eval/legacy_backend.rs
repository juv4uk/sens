//! Explicit compatibility/backend bridge for historical exact-eight mechanisms.
//!
//! Domain identity is selected before this module is entered. This boundary
//! may materialize a historical byte as Sens8 solely to invoke or alias an
//! implementation that has not yet been rewritten domain-native.

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
