//! SID-keyed projection for evaluator mechanisms that require special
//! evaluation order.
//!
//! Contract 9 / #1325: function identity is only Sid8. Human surfaces are
//! resolved through the shared registry, and this module answers only whether
//! an already-resolved SID selects one of the evaluator mechanisms projected
//! from `lib/evaluator-dispatch.lisp`.
//!
//! There is deliberately no named function-identity enum here.

use crate::semantic_registry;
use crate::Sid8;

mod generated {
    include!("necessary_forms_generated.rs");
}

fn contains_sid(rows: &[u8], sid: Sid8) -> bool {
    rows.contains(&sid.packed_byte())
}

pub(crate) fn is_lambda_sid(sid: Sid8) -> bool {
    contains_sid(generated::LAMBDA_FORM_SIDS, sid)
}

pub(crate) fn is_define_sid(sid: Sid8) -> bool {
    contains_sid(generated::DEFINE_FORM_SIDS, sid)
}

pub(crate) fn is_necessary_form_sid(sid: Sid8) -> bool {
    is_lambda_sid(sid) || is_define_sid(sid)
}

/// Resolve an executable list-head surface through the shared registry and
/// return the exact SID only when that SID is routed through one of the
/// evaluator mechanisms above.
pub(crate) fn routed_sid_for_symbol(name: &str) -> Option<Sid8> {
    let sid = semantic_registry::admitted_semantic_id_for_surface(name)?;
    is_necessary_form_sid(sid).then_some(sid)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn eight_bit_source_token_is_not_a_surface_name() {
        assert_eq!(routed_sid_for_symbol("00001001"), None);
        assert_eq!(routed_sid_for_symbol("0000SID 11"), None);
    }

    #[test]
    fn exact_sids_select_only_their_evaluator_mechanisms() {
        assert!(is_lambda_sid(crate::sid!(00001000)));
        assert!(is_define_sid(crate::sid!(00001001)));
        assert!(is_define_sid(crate::sid!(00001011)));

        assert!(!is_define_sid(crate::sid!(00001000)));
        assert!(!is_lambda_sid(crate::sid!(00001001)));
        assert!(!is_necessary_form_sid(crate::sid!(00001100)));
    }

    #[test]
    fn every_peer_surface_routes_to_the_same_exact_sid() {
        for expected_sid in [
            crate::sid!(00001000),
            crate::sid!(00001001),
            crate::sid!(00001011),
        ] {
            let surfaces =
                semantic_registry::admitted_surfaces_for_semantic_id(expected_sid);
            assert!(
                !surfaces.is_empty(),
                "{expected_sid} should expose at least one admitted surface"
            );
            for surface in &surfaces {
                assert_eq!(
                    routed_sid_for_symbol(surface),
                    Some(expected_sid),
                    "surface {surface:?} must route only to its exact SID"
                );
            }
        }
    }

    #[test]
    fn def_keeps_its_own_sid_but_selects_the_define_mechanism() {
        let sid = semantic_registry::semantic_id_for_surface("def")
            .expect("def must remain present in the semantic registry");
        assert_eq!(sid, crate::sid!(00001011));
        assert_eq!(routed_sid_for_symbol("def"), Some(sid));
        assert!(is_define_sid(sid));
    }

    #[test]
    fn unrelated_registry_rows_do_not_gain_necessary_form_routing() {
        assert_eq!(
            semantic_registry::semantic_id_for_surface("+"),
            Some(crate::sid!(00001100))
        );
        assert_eq!(routed_sid_for_symbol("+"), None);
        assert!(!is_necessary_form_sid(crate::sid!(00001100)));
    }
}
