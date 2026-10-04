//! Runtime projection of the Lisp-owned semantic registry.
//!
//! The canonical authority is lib/surface/semantic-registry.lisp and its
//! Lisp-owned reader/API. This module contains no parser for canonical source
//! text. The generated table is emitted by
//! scripts/generate-rust-semantic-registry.lisp and is only a mechanical
//! runtime projection for fast lookup.
//
//! Generated rows may carry a packed byte as substrate representation of an
//! already understood Lisp Binary identity. This wrapper converts that byte to
//! opaque Sens8 immediately; runtime registry APIs never expose decimal IDs.

use std::{collections::HashMap, sync::OnceLock};

use crate::{Bija3, Bit3, Bit4, Bit5, CoreD4, CoreD5, CoreDomainIdentity, DomainIdentity};
use crate::Sens8;

mod generated {
    include!("semantic_registry_generated.rs");
}

mod domain_surface_generated {
    include!("domain_surface_registry_generated.rs");
}

use domain_surface_generated::DOMAIN_SURFACE_ROWS;
use generated::{SemanticRow, SEMANTIC_ROWS};

pub(crate) type SemanticId = Sens8;

fn exact_domain_identity_from_projection(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    match width {
        3 => Some(CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(bits)?))),
        4 => Some(CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(bits)?))),
        _ => None,
    }
}

/// Direct D3/D4 human-surface projection.
///
/// This path consumes the exact-domain projection generated from
/// lib/surface/domain-surfaces-d1-d4.lisp. It never consults a historical
/// packed byte to recover domain identity.
fn direct_domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    DOMAIN_SURFACE_ROWS.iter().find_map(|row| {
        let matches_human_surface = row.source_routable
            && row
                .surfaces
                .iter()
                .any(|surface| matches!(surface.namespace, "uk" | "sa") && surface.name == name);
        matches_human_surface
            .then(|| exact_domain_identity_from_projection(row.width, row.bits))
            .flatten()
    })
}

pub(crate) fn legacy_domain_identity_from_registry_byte(byte: u8) -> Option<CoreDomainIdentity> {
    let d3 = |raw| CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()));
    let d4 = |raw| CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()));
    match byte {
        0b0000_0001 => Some(d3(0b001)), // QUOTE
        0b0000_0010 => Some(d3(0b010)), // ATOM
        0b0000_0111 => Some(d3(0b110)), // COND
        0b0000_0100 => Some(d3(0b111)), // CONS
        0b0000_0101 => Some(d3(0b100)), // CAR
        0b0000_0110 => Some(d3(0b011)), // CDR
        0b0000_0011 => Some(d3(0b101)), // EQ
        0b0000_1000 => Some(d4(0b0010)), // LAMBDA
        0b0000_1001 => Some(d4(0b0011)), // DEFINE
        0b0010_1001 => Some(d4(0b1111)), // APPEND
        // Existing selector surfaces project explicitly to their ratified D4
        // identities. This is semantic-role mapping, never byte truncation.
        0b0011_0011 => Some(d4(0b1000)), // CAAR
        0b0011_0100 => Some(d4(0b1001)), // CADR
        0b0011_0101 => Some(d4(0b0111)), // CDDR
        _ => None,
    }
}

/// Binding-only OD-005 bootstrap projection for Lisp-owned definitions.
///
/// This MUST NOT be used to reinterpret historical Sens8 calls. Its only
/// consumer is `bind_language_definition`: a definition discovered through
/// the compatibility surface registry is bound once into an already-ratified
/// exact D5 slot. #3062 removes this bootstrap detour.
pub(crate) fn transitional_d5_binding_identity_from_registry_byte(
    byte: u8,
) -> Option<CoreDomainIdentity> {
    let d5 = |raw| CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(raw).unwrap()));
    match byte {
        0b0010_1010 => Some(d5(0b10100)), // REVERSE
        0b0001_0100 => Some(d5(0b10111)), // QUOTIENT
        0b0010_1101 => Some(d5(0b11100)), // ASSOC
        0b0010_1100 => Some(d5(0b11101)), // MEMBER
        0b1010_1100 => Some(d5(0b11111)), // SUBST
        _ => None,
    }
}
/// Current staged surface lookup.
///
/// Ukrainian and Sanskrit D3/D4 spellings resolve directly through the
/// exact-domain projection. The byte-backed lookup remains only as a bounded
/// compatibility fallback for still-unmigrated spellings.
pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    direct_domain_identity_for_surface(name).or_else(|| {
        registry_byte_for_surface(name).and_then(legacy_domain_identity_from_registry_byte)
    })
}

pub(crate) fn surface_for_domain_identity(
    identity: DomainIdentity,
    namespace: &str,
) -> Option<&'static str> {
    DOMAIN_SURFACE_ROWS
        .iter()
        .find(|row| {
            usize::from(row.width) == identity.width() && row.bits == identity.packed_bits()
        })?
        .surfaces
        .iter()
        .find_map(|surface| (surface.namespace == namespace).then_some(surface.name))
}
pub(crate) fn semantic_id_bits(semantic_id: SemanticId) -> String {
    semantic_id.to_string()
}

fn live_rows() -> &'static [SemanticRow] {
    SEMANTIC_ROWS
}

fn registry_byte_for_surface(name: &str) -> Option<u8> {
    live_rows()
        .iter()
        .find(|row| row.surfaces.iter().any(|surface| surface.name == name))
        .map(|row| row.semantic_id)
}


pub(crate) fn admitted_semantic_ids() -> Vec<SemanticId> {
    live_rows()
        .iter()
        .map(|row| Sens8::from_packed_byte(row.semantic_id))
        .collect()
}

fn insert_surface_mapping(
    index: &mut HashMap<&'static str, SemanticId>,
    surface: &'static str,
    semantic_id: SemanticId,
) {
    if let Some(previous) = index.insert(surface, semantic_id) {
        if previous != semantic_id {
            panic!(
                "generated semantic registry surface must be unique: {surface} maps to both {} and {}",
                semantic_id_bits(previous),
                semantic_id_bits(semantic_id)
            );
        }
    }
}

fn surface_index() -> &'static HashMap<&'static str, SemanticId> {
    static INDEX: OnceLock<HashMap<&'static str, SemanticId>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in live_rows() {
            for surface in row.surfaces {
                insert_surface_mapping(&mut index, surface.name, Sens8::from_packed_byte(row.semantic_id));
            }
        }
        index
    })
}

pub(crate) fn admitted_semantic_id_for_surface(name: &str) -> Option<SemanticId> {
    surface_index().get(name).copied()
}

fn stable_surfaces_from_index(
    index: &HashMap<&'static str, SemanticId>,
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    let mut surfaces = index
        .iter()
        .filter_map(|(surface, mapped_id)| (*mapped_id == semantic_id).then_some(*surface))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

fn admitted_surfaces_from_rows(
    rows: &[SemanticRow],
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    let mut surfaces = rows
        .iter()
        .find(|row| row.semantic_id == semantic_id.packed_byte())
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|surface| surface.name))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

pub(crate) fn semantic_id_for_surface(name: &str) -> Option<SemanticId> {
    admitted_semantic_id_for_surface(name)
}

pub(crate) fn stable_surfaces_for_semantic_id(
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    stable_surfaces_from_index(surface_index(), semantic_id)
}

pub(crate) fn admitted_surfaces_for_semantic_id(
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    admitted_surfaces_from_rows(live_rows(), semantic_id)
}

pub(crate) fn admitted_surfaces_with_namespace_for_semantic_id(
    semantic_id: SemanticId,
) -> Vec<(&'static str, &'static str)> {
    let mut surfaces = live_rows()
        .iter()
        .find(|row| row.semantic_id == semantic_id.packed_byte())
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|s| (s.namespace, s.name)))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

#[cfg(test)]
mod tests {
    use super::*;
    use generated::SemanticSurface;

    #[test]
    fn migrated_registry_roles_are_domain_qualified_and_not_truncated() {
        let d3_110 = domain_identity_for_surface("за-умовою").unwrap();
        let d3_101 = domain_identity_for_surface("тотожне?").unwrap();
        let d4_0010 = domain_identity_for_surface("функція").unwrap();
        let d4_0011 = domain_identity_for_surface("визначити").unwrap();

        assert_eq!((d3_110.width(), d3_110.packed_bits()), (3, 0b110));
        assert_eq!((d3_101.width(), d3_101.packed_bits()), (3, 0b101));
        assert_eq!((d4_0010.width(), d4_0010.packed_bits()), (4, 0b0010));
        assert_eq!((d4_0011.width(), d4_0011.packed_bits()), (4, 0b0011));

        assert_ne!(d3_110.packed_bits(), 0b011);
        assert_ne!(d3_101.packed_bits(), 0b111);
        assert_ne!(d4_0010.packed_bits(), 0b1000);
        assert_ne!(d4_0011.packed_bits(), 0b1001);
    }

    #[test]
    fn existing_selector_surfaces_project_to_ratified_d4() {
        for (surface, bits) in [
            ("перше-від-першого", 0b1000),
            ("перше-від-решти", 0b1001),
            ("решта-від-першого", 0b0110),
            ("решта-від-решти", 0b0111),
        ] {
            let identity = domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("selector surface must project: {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (4, bits));
        }
    }

    #[test]
    fn lisp_owned_d5_binding_projection_is_explicit_but_not_global_legacy_meaning() {
        for (legacy_byte, bits) in [
            (0b0010_1010, 0b10001),
            (0b0001_0100, 0b10011),
            (0b0010_1101, 0b11100),
            (0b0010_1100, 0b11101),
            (0b1010_1100, 0b11111),
        ] {
            let identity = transitional_d5_binding_identity_from_registry_byte(legacy_byte)
                .expect("ratified D5 bootstrap binding projection");
            assert_eq!((identity.width(), identity.packed_bits()), (5, bits));

            // A historical byte remains a historical byte during invocation.
            // Only definition binding is allowed to consult the D5 bootstrap map.
            assert_eq!(legacy_domain_identity_from_registry_byte(legacy_byte), None);
        }
    }
    #[test]
    fn append_surface_projects_only_to_ratified_d4() {
        let identity = domain_identity_for_surface("приєднати")
            .expect("D4:1111 surface must project to ratified D4");
        assert_eq!((identity.width(), identity.packed_bits()), (4, 0b1111));
        assert_eq!(
            transitional_d5_binding_identity_from_registry_byte(0b0010_1001),
            None,
            "APPEND must not retain a transitional D5 binding"
        );
    }

    #[test]
    fn unmigrated_registry_rows_have_no_fake_domain_identity() {
        assert_eq!(domain_identity_for_surface("+"), None);
    }

    #[test]
    fn uk_sa_exact_domain_projection_does_not_need_a_legacy_byte_route() {
        for (surface, width, bits) in [
            ("aṇu?", 3, 0b010),
            ("решта-від-першого", 4, 0b0110),
            ("phalana", 4, 0b0010),
            ("saṅkalana", 4, 0b1111),
        ] {
            let identity = direct_domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("exact-domain surface must resolve directly: {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (width, bits));
            assert_eq!(domain_identity_for_surface(surface), Some(identity));
        }

        assert_eq!(
            registry_byte_for_surface("aṇu?")
                .and_then(legacy_domain_identity_from_registry_byte),
            None,
            "new Sanskrit ATOM spelling must not depend on a historical byte"
        );
        assert_eq!(
            registry_byte_for_surface("решта-від-першого")
                .and_then(legacy_domain_identity_from_registry_byte),
            None,
            "CDAR must be admitted by D4 projection even without a legacy byte mapping"
        );
    }

    #[test]
    fn generated_registry_is_one_contiguous_byte_axis() {
        assert_eq!(SEMANTIC_ROWS.len(), 256);
        for (expected, row) in SEMANTIC_ROWS.iter().enumerate() {
            assert_eq!(usize::from(row.semantic_id), expected);
        }
        assert_eq!(SEMANTIC_ROWS.first().map(|row| row.semantic_id), Some(0));
        assert_eq!(SEMANTIC_ROWS.last().map(|row| row.semantic_id), Some(255));
    }

    #[test]
    fn reverse_projection_covers_d1_d4_without_making_structure_callable() {
        let yes = DomainIdentity::D1(crate::PredicateBit::from_word(crate::Bit1::new(1).unwrap()));
        let open = DomainIdentity::D2(crate::Racana2::from_word(crate::Bit2::new(0b10).unwrap()));
        let empty = DomainIdentity::D3(crate::Bija3::from_word(crate::Bit3::new(0b000).unwrap()));
        let lambda = DomainIdentity::D4(crate::CoreD4::from_word(crate::Bit4::new(0b0010).unwrap()));

        assert_eq!(surface_for_domain_identity(yes, "uk"), Some("так"));
        assert_eq!(surface_for_domain_identity(yes, "sa"), Some("ām"));
        assert_eq!(surface_for_domain_identity(open, "uk"), Some("відкрити"));
        assert_eq!(surface_for_domain_identity(empty, "sa"), Some("śūnya"));
        assert_eq!(surface_for_domain_identity(lambda, "uk"), Some("функція"));
        assert_eq!(surface_for_domain_identity(lambda, "sa"), Some("phalana"));

        assert_eq!(direct_domain_identity_for_surface("так"), None);
        assert_eq!(direct_domain_identity_for_surface("відкрити"), None);
        assert_eq!(direct_domain_identity_for_surface("порожнє"), None);
    }

    #[test]
    fn generated_registry_contains_fixed_surface_namespaces() {
        let quote = &SEMANTIC_ROWS[1].surfaces;
        assert!(quote.contains(&SemanticSurface { namespace: "en", name: "quote" }));
        assert!(quote.contains(&SemanticSurface { namespace: "ук", name: "як-є" }));
        assert!(quote.contains(&SemanticSurface { namespace: "укр", name: "як-є" }));
        assert!(quote.contains(&SemanticSurface { namespace: "sa", name: "svarūpa" }));
        assert!(quote.contains(&SemanticSurface { namespace: "sym", name: "'" }));
    }

    #[test]
    fn binary_spelling_is_identity_not_a_surface() {
        assert_eq!(semantic_id_for_surface("00001010"), None);
        assert_eq!(semantic_id_for_surface("10101000"), None);
    }

    #[test]
    fn public_reverse_projection_preserves_identity() {
        for surface in admitted_surfaces_for_semantic_id(crate::sens!(00001111)) {
            assert_eq!(
                crate::semantic_registry_export::semantic_id_for_admitted_surface(surface),
                Some(crate::sens!(00001111))
            );
        }
        assert_eq!(
            crate::semantic_registry_export::semantic_id_for_admitted_surface("not-a-surface"),
            None
        );
    }

    #[test]
    fn unrelated_rows_are_projected_without_assigning_evaluator_meaning() {
        assert_eq!(semantic_id_for_surface("+"), Some(crate::sens!(00001100)));
    }

    #[test]
    fn surfaces_with_namespace_align_with_present_names_and_keep_namespace() {
        let with_namespace = admitted_surfaces_with_namespace_for_semantic_id(crate::sens!(00000001));
        let names_only = admitted_surfaces_for_semantic_id(crate::sens!(00000001));
        assert_eq!(with_namespace.len(), names_only.len());
        assert!(with_namespace.contains(&("en", "quote")));
        assert!(with_namespace.contains(&("ук", "як-є")));
        assert!(with_namespace.contains(&("sym", "'")));
    }
}
