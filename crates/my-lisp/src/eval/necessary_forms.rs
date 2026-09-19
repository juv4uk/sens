//! Immutable routing for evaluator mechanisms necessary beyond Canon 0 + McCarthy7.
//!
//! Stable human/symbolic spellings are resolved by the shared semantic registry.
//! This module owns only the mapping from opaque numeric semantic IDs to the
//! evaluator mechanisms for DEFINE and LAMBDA.

use crate::semantic_registry::{self, SemanticId};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum NecessaryFormIdentity {
    Define,
    Lambda,
}

pub(crate) const LAMBDA_SEMANTIC_ID: SemanticId = 8;
pub(crate) const DEFINE_SEMANTIC_ID: SemanticId = 9;
/// `def` -- a compatibility-only spelling for the same Define meaning as
/// `define`/`визначити`, under its own semantic ID in
/// `lib/surface/semantic-registry.wsm` rather than sharing 0011's row.
pub(crate) const DEF_COMPATIBILITY_SEMANTIC_ID: SemanticId = 11;

fn identity_for_semantic_id(semantic_id: SemanticId) -> Option<NecessaryFormIdentity> {
    match semantic_id {
        DEFINE_SEMANTIC_ID | DEF_COMPATIBILITY_SEMANTIC_ID => Some(NecessaryFormIdentity::Define),
        LAMBDA_SEMANTIC_ID => Some(NecessaryFormIdentity::Lambda),
        _ => None,
    }
}

/// Resolve an executable list-head symbol through the shared authority
/// registry, then select the evaluator mechanism by numeric semantic ID.
/// Uses the admitted (stable OR compatibility-only) surface index, not the
/// stable-only one `canon.rs`/tooling use elsewhere: `def`'s row is
/// compatibility-only, and dispatch must still see it as Define through
/// the registry rather than through a hardcoded `"def"` literal
/// (previously duplicated in both `eval/mod.rs` and `ir.rs` for exactly
/// this reason -- both removed once this function could see it).
pub(crate) fn identity_for_symbol(name: &str) -> Option<NecessaryFormIdentity> {
    semantic_registry::admitted_semantic_id_for_surface(name).and_then(identity_for_semantic_id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn byte_sid_is_not_a_surface_spelling() {
        assert_eq!(identity_for_symbol("00001001"), None);
        assert_eq!(identity_for_symbol("0000SID 11"), None);
        assert_eq!(identity_for_semantic_id(DEFINE_SEMANTIC_ID), Some(NecessaryFormIdentity::Define));
        assert_eq!(identity_for_semantic_id(LAMBDA_SEMANTIC_ID), Some(NecessaryFormIdentity::Lambda));
    }

    #[test]
    fn every_admitted_surface_for_define_and_lambda_is_a_registry_driven_peer_spelling() {
        // Which spellings mean "define"/"lambda" (визначити/define,
        // функція/lambda, ...) is a semantic-registry FACT, not Rust
        // knowledge to enumerate here -- this test asserts only the
        // implementation invariant: whatever surfaces the registry admits
        // for SIDs 9/8 all route through this same numeric-ID dispatch,
        // regardless of which language they're spelled in.
        for (semantic_id, identity) in [
            (DEFINE_SEMANTIC_ID, NecessaryFormIdentity::Define),
            (LAMBDA_SEMANTIC_ID, NecessaryFormIdentity::Lambda),
        ] {
            let surfaces = semantic_registry::admitted_surfaces_for_semantic_id(semantic_id);
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
    fn compatibility_only_def_still_resolves_to_define_through_the_registry() {
        // `def`'s row (SID 11) is compatibility-only, not stable -- this is
        // the fact that used to make dispatch fall back to a hardcoded
        // `"def"` literal in eval/mod.rs and a matching one in ir.rs,
        // because the stable-only surface index cannot see it. Both were
        // removed once identity_for_symbol started using the admitted
        // (stable-or-compatibility-only) index instead.
        assert_eq!(
            semantic_registry::semantic_id_for_surface("def"),
            None,
            "def's row is deliberately compatibility-only, not stable"
        );
        assert_eq!(
            semantic_registry::admitted_semantic_id_for_surface("def"),
            Some(DEF_COMPATIBILITY_SEMANTIC_ID)
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
    fn synthetic_registry_constructively_controls_necessary_form_routing() {
        const SYNTHETIC: &str =
            "(sr/2\n  (\"00000000\" ())\n  (\"00001000\" (xx comet))\n  (\"00001001\" (xx asteroid))\n)";
        let index = semantic_registry::build_surface_index(SYNTHETIC);

        let route = |surface: &str| {
            index
                .get(surface)
                .copied()
                .and_then(identity_for_semantic_id)
        };

        assert_eq!(route("comet"), Some(NecessaryFormIdentity::Lambda));
        assert_eq!(route("asteroid"), Some(NecessaryFormIdentity::Define));
        assert_eq!(route("lambda"), None);
        assert_eq!(route("define"), None);
    }

    #[test]
    fn unrelated_registry_rows_do_not_gain_necessary_form_meaning() {
        assert_eq!(semantic_registry::semantic_id_for_surface("+"), Some(12));
        assert_eq!(identity_for_symbol("+"), None);
    }
}
