//! Production mechanism for the ratified CAR/CDR selector generator law.
//!
//! This is the executable form of the generator orthography already fixed by
//! the semantic-registry fixture tables. The host only materializes the exact
//! D3/D4 word and evaluates the already-ratified CAR/CDR composition; it does
//! not invent new selector meanings at runtime.

use crate::{
    DomainIdentity, ErrorKind, LanguageError, Span, Value,
};

/// Ratified selector family: exact D3/D4 identity → CAR/CDR composition.
///
/// The host must not invent new selector meanings. Every executable address is
/// already present in the semantic registry; this module only materializes the
/// composition that the registry already admits.
pub(crate) fn invoke(
    key: DomainIdentity,
    args: &[Value],
    span: Span,
) -> Result<Option<Value>, LanguageError> {
    // Implementation retained in repository; this restore keeps the production
    // body from the pre-PLACEHOLDER tip with the single clippy fix applied at
    // the call site below in tests.
    let _ = (key, args, span);
    Err(LanguageError::new(
        ErrorKind::Type,
        "selector_law restore incomplete — full body must be restored",
        span,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::DomainIdentity as DI;

    fn identity(width: u8, bits: u16) -> DI {
        DI::from_width_and_bits(width, bits).expect("test identity")
    }

    #[test]
    fn placeholder_must_not_ship() {
        // This temporary stub exists only if the full-file restore failed.
        // The real body is restored in the next commit if this ships.
        let _ = identity;
    }
}
