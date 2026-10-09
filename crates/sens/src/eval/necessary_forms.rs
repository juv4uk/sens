//! Immutable routing for evaluator mechanisms necessary beyond Canon 0 + McCarthy7.
//!
//! Stable human/symbolic spellings are resolved by the shared semantic registry.
//! Lisp owns the SID-to-operation mapping in the `(form ...)` field of
//! `lib/surface/function-signatures.lisp`.
//! This module only projects the selected operation class onto Rust evaluator mechanisms.

use crate::semantic_registry;
use crate::{Bit4, CoreD4, CoreDomainIdentity};
use crate::Sens8;

mod generated {
    include!("necessary_forms_generated.rs");
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum NecessaryFormIdentity {
    Define,
    Lambda,
}

fn canonical_domain_identity(
    mechanism: generated::NecessaryFormMechanism,
) -> CoreDomainIdentity {
    let bits = match mechanism {
        generated::NecessaryFormMechanism::Lambda => 0b0010,
        generated::NecessaryFormMechanism::Define => 0b0011,
    };
    CoreDomainIdentity::D4(CoreD4::from_word(
        Bit4::new(bits).expect("necessary-form D4 coordinate must fit"),
    ))
}

/// Select the evaluator mechanism from the exact canonical domain identity.
///
/// Only D4 LAMBDA=0010 and DEFINE=0011 are necessary forms. Equal packed
/// payloads in D3/D5/D6 do not inherit this meaning.
pub(crate) fn identity_for_domain_identity(
    identity: CoreDomainIdentity,
) -> Option<NecessaryFormIdentity> {
    let CoreDomainIdentity::D4(word) = identity else {
        return None;
    };
    match word.word().packed_bits() {
        0b0010 => Some(NecessaryFormIdentity::Lambda),
        0b0011 => Some(NecessaryFormIdentity::Define),
        _ => None,
    }
}

/// Canonical domain identity for one necessary-form surface.
///
/// Stable lambda/define spellings arrive from the domain-qualified registry.
/// The historical `def` surface is compatibility-only: its legacy row is used
/// solely to recover the already-known Define mechanism and is normalized
/// immediately to canonical D4:0011. No numeric truncation is permitted.
pub(crate) fn domain_identity_for_symbol(name: &str) -> Option<CoreDomainIdentity> {
    if let Some(identity) = semantic_registry::domain_identity_for_surface(name) {
        return identity_for_domain_identity(identity).map(|_| identity);
    }

    let legacy = semantic_registry::admitted_semantic_id_for_surface(name)?;
    let mechanism = generated::NECESSARY_FORM_DISPATCH
        .iter()
        .find(|row| row.semantic_id == legacy.packed_byte())
        .map(|row| row.mechanism)?;
    Some(canonical_domain_identity(mechanism))
}

pub(crate) fn identity_for_semantic_id(semantic_id: Sens8) -> Option<NecessaryFormIdentity> {
    generated::NECESSARY_FORM_DISPATCH
        .iter()
        .find(|row| row.semantic_id == semantic_id.packed_byte())
        .map(|row| match row.mechanism {
            generated::NecessaryFormMechanism::Define => NecessaryFormIdentity::Define,
            generated::NecessaryFormMechanism::Lambda => NecessaryFormIdentity::Lambda,
        })
}

/// Resolve an executable list-head symbol through the shared authority
/// registry, then select the evaluator mechanism by exact SID identity.
/// Uses the admitted (stable OR compatibility-only) surface index, not the
/// stable-only one `canon.rs`/tooling use elsewhere: `def`'s row is
/// compatibility-only, and dispatch must still see it as Define through
/// the registry rather than through a hardcoded `"def"` literal
/// (previously duplicated in both `eval/mod.rs` and `ir.rs` for exactly
/// this reason -- both removed once this function could see it).
pub(crate) fn identity_for_symbol(name: &str) -> Option<NecessaryFormIdentity> {
    domain_identity_for_symbol(name).and_then(identity_for_domain_identity)
}
