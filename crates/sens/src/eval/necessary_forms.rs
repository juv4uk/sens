//! Immutable routing for evaluator mechanisms necessary beyond Canon 0 + McCarthy7.
//!
//! Stable human/symbolic spellings are resolved by the shared semantic registry.
//! Lisp owns the SID-to-operation mapping in the `(form ...)` field of
//! `lib/surface/function-signatures.lisp`.
//! This module only projects the selected operation class onto Rust evaluator mechanisms.

use crate::{legacy_registry, semantic_registry};
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
    if let Some(identity) =
        semantic_registry::domain_identity_for_surface(name).and_then(|identity| identity.core_operation())
    {
        return identity_for_domain_identity(identity).map(|_| identity);
    }

    let legacy = legacy_registry::id_for_surface(name)?;
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_domain_controls_necessary_form_routing() {
        let d4_0010 = domain_identity_for_symbol("функція").expect("D4:0010 identity");
        let d4_0011 = domain_identity_for_symbol("визначити").expect("D4:0011 identity");

        assert_eq!((d4_0010.width(), d4_0010.packed_bits()), (4, 0b0010));
        assert_eq!((d4_0011.width(), d4_0011.packed_bits()), (4, 0b0011));
        assert_eq!(
            identity_for_domain_identity(d4_0010),
            Some(NecessaryFormIdentity::Lambda)
        );
        assert_eq!(
            identity_for_domain_identity(d4_0011),
            Some(NecessaryFormIdentity::Define)
        );

        let d3_atom = crate::CoreDomainIdentity::D3(crate::Bija3::from_word(
            crate::Bit3::new(0b010).unwrap(),
        ));
        let d3_cond = crate::CoreDomainIdentity::D3(crate::Bija3::from_word(
            crate::Bit3::new(0b011).unwrap(),
        ));
        assert_eq!(identity_for_domain_identity(d3_atom), None);
        assert_eq!(identity_for_domain_identity(d3_cond), None);
    }

    #[test]
    fn byte_sid_is_not_a_surface_spelling() {
        assert_eq!(identity_for_symbol("00001001"), None);
        assert_eq!(identity_for_symbol("0000SID 11"), None);
        let define_id = legacy_registry::id_for_surface("define")
            .expect("define must have one admitted semantic identity");
        let lambda_id = legacy_registry::id_for_surface("lambda")
            .expect("lambda must have one admitted semantic identity");
        assert_eq!(identity_for_semantic_id(define_id), Some(NecessaryFormIdentity::Define));
        assert_eq!(identity_for_semantic_id(lambda_id), Some(NecessaryFormIdentity::Lambda));
    }

    #[test]
    fn every_admitted_surface_for_define_and_lambda_is_a_registry_driven_peer_spelling() {
        // Which spellings mean "define"/"lambda" (визначити/define,
        // функція/lambda, ...) is a semantic-registry FACT, not Rust
        // knowledge to enumerate here -- this test asserts only the
        // implementation invariant: whatever surfaces the registry admits
        // for SIDs 9/8 all route through this same SID dispatch,
        // regardless of which language they're spelled in.
        for (surface, identity) in [
            ("define", NecessaryFormIdentity::Define),
            ("lambda", NecessaryFormIdentity::Lambda),
        ] {
            let semantic_id = legacy_registry::id_for_surface(surface)
                .expect("necessary form must have one admitted semantic identity");
            let surfaces = legacy_registry::admitted_surfaces_for_id(semantic_id);
            assert!(
                surfaces.len() >= 2,
                "{semantic_id} should admit at least two surfaces for this invariant to be \
                 meaningful, got {surfaces:?}"
            );
            for surface in &surfaces {
                assert_eq!(
                    identity_for_symbol(surface),
                    Some(identity),
                    "registry-admitted surface {surface:?} for {semantic_id} did not route to \
                     {identity:?}"
                );
            }
        }
    }

    #[test]
    fn def_resolves_to_define_through_status_free_registry() {
        // Status-free canonical semantic registry has no compatibility-only admission class.
        // A present spelling is directly routable; SID 11 still maps to the
        // compatibility `def` form without any hardcoded spelling fallback.
        let def_id = legacy_registry::id_for_surface("def")
            .expect("def must remain present in the semantic registry");
        assert_eq!(
            legacy_registry::id_for_surface("def"),
            Some(def_id)
        );
        assert_eq!(
            identity_for_semantic_id(def_id),
            Some(NecessaryFormIdentity::Define)
        );
        assert_eq!(identity_for_symbol("def"), Some(NecessaryFormIdentity::Define));
    }

    #[test]
    fn non_stable_or_unrelated_spellings_do_not_gain_necessary_form_identity() {
        assert_eq!(identity_for_symbol("00001000"), None);
        assert_eq!(identity_for_symbol("id00001000"), None);
        assert_eq!(identity_for_symbol("quote"), None);
    }

    #[test]
    fn exact_sid_identities_control_necessary_form_routing() {
        assert_eq!(
            identity_for_semantic_id(
                legacy_registry::id_for_surface("lambda")
                    .expect("lambda semantic identity")
            ),
            Some(NecessaryFormIdentity::Lambda)
        );
        assert_eq!(
            identity_for_semantic_id(
                legacy_registry::id_for_surface("define")
                    .expect("define semantic identity")
            ),
            Some(NecessaryFormIdentity::Define)
        );
        assert_eq!(
            identity_for_semantic_id(
                legacy_registry::id_for_surface("def")
                    .expect("def compatibility semantic identity")
            ),
            Some(NecessaryFormIdentity::Define)
        );
    }

    #[test]
    fn unrelated_registry_rows_do_not_gain_necessary_form_meaning() {
        assert_eq!(legacy_registry::id_for_surface("+"), Some(crate::sens!(00001100)));
        assert_eq!(identity_for_symbol("+"), None);
    }
}
