//! Canonical domain-qualified routing for evaluator mechanisms beyond D3.
//!
//! This module owns only exact-domain necessary-form identity. Historical
//! exact-eight compatibility routing lives in `necessary_forms_legacy.rs`.
//! Human spellings are resolved by the semantic registry; canonical meaning is
//! carried by `CoreDomainIdentity`, never reconstructed from packed bytes.

use crate::semantic_registry;
use crate::{Bit4, CoreD4, CoreDomainIdentity};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum NecessaryFormIdentity {
    Define,
    Lambda,
}

fn canonical_domain_identity(identity: NecessaryFormIdentity) -> CoreDomainIdentity {
    let bits = match identity {
        NecessaryFormIdentity::Lambda => 0b0010,
        NecessaryFormIdentity::Define => 0b0011,
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
/// Stable LAMBDA/DEFINE spellings resolve through the domain-qualified registry.
/// Historical compatibility spellings (currently `def`) are delegated to the
/// explicit legacy adapter, which returns only a mechanism class; this module
/// then normalizes that class to the canonical D4 coordinate.
pub(crate) fn domain_identity_for_symbol(name: &str) -> Option<CoreDomainIdentity> {
    if let Some(identity) = semantic_registry::domain_identity_for_surface(name) {
        return identity_for_domain_identity(identity).map(|_| identity);
    }

    super::necessary_forms_legacy::identity_for_symbol(name).map(canonical_domain_identity)
}

pub(crate) fn identity_for_symbol(name: &str) -> Option<NecessaryFormIdentity> {
    domain_identity_for_symbol(name).and_then(identity_for_domain_identity)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Bit5, Bit6, CoreD5, CoreD6};

    #[test]
    fn exact_domain_controls_necessary_form_routing() {
        let lambda = domain_identity_for_symbol("lambda").expect("lambda D4 identity");
        let define = domain_identity_for_symbol("define").expect("define D4 identity");
        let compat_def = domain_identity_for_symbol("def").expect("def normalizes to DEFINE");

        assert_eq!((lambda.width(), lambda.packed_bits()), (4, 0b0010));
        assert_eq!((define.width(), define.packed_bits()), (4, 0b0011));
        assert_eq!(compat_def, define);
        assert_eq!(
            identity_for_domain_identity(lambda),
            Some(NecessaryFormIdentity::Lambda)
        );
        assert_eq!(
            identity_for_domain_identity(define),
            Some(NecessaryFormIdentity::Define)
        );
    }

    #[test]
    fn equal_payloads_in_other_domains_do_not_inherit_d4_meaning() {
        let d3 = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b010).unwrap()));
        let d5 = CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b00010).unwrap()));
        let d6 = CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(0b000010).unwrap()));

        assert_eq!(identity_for_domain_identity(d3), None);
        assert_eq!(identity_for_domain_identity(d5), None);
        assert_eq!(identity_for_domain_identity(d6), None);
    }

    #[test]
    fn byte_shaped_text_is_not_a_surface_spelling() {
        assert_eq!(identity_for_symbol("00001001"), None);
        assert_eq!(identity_for_symbol("0000SID 11"), None);
    }

    #[test]
    fn admitted_peer_spellings_converge_on_canonical_d4_identity() {
        for (surface, expected) in [
            ("define", NecessaryFormIdentity::Define),
            ("lambda", NecessaryFormIdentity::Lambda),
        ] {
            let canonical = domain_identity_for_symbol(surface)
                .expect("necessary form must have canonical domain identity");
            let legacy = semantic_registry::admitted_semantic_id_for_surface(surface)
                .expect("surface must remain admitted during compatibility migration");
            let peers = semantic_registry::admitted_surfaces_for_semantic_id(legacy);
            assert!(peers.len() >= 2);

            for peer in peers {
                assert_eq!(identity_for_symbol(peer), Some(expected));
                assert_eq!(
                    domain_identity_for_symbol(peer).map(CoreDomainIdentity::width),
                    Some(4)
                );
            }

            assert_eq!(identity_for_domain_identity(canonical), Some(expected));
        }
    }

    #[test]
    fn unrelated_surfaces_do_not_gain_necessary_form_identity() {
        assert_eq!(identity_for_symbol("quote"), None);
        assert_eq!(identity_for_symbol("+"), None);
    }
}
