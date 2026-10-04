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

use crate::{Bija3, Bit3, Bit4, Bit5, CoreD4, CoreD5, CoreDomainIdentity};
use crate::Sens8;

mod generated {
    include!("semantic_registry_generated.rs");
}

use generated::{SemanticRow, SEMANTIC_ROWS};

pub(crate) type SemanticId = Sens8;

pub(crate) fn legacy_domain_identity_from_registry_byte(byte: u8) -> Option<CoreDomainIdentity> {
    let d3 = |raw| CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()));
    let d4 = |raw| CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()));
    let d5 = |raw| CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(raw).unwrap()));
    match byte {
        0b0000_0001 => Some(d3(0b001)), // QUOTE
        0b0000_0010 => Some(d3(0b010)), // ATOM
        0b0000_0111 => Some(d3(0b011)), // COND
        0b0000_0100 => Some(d3(0b100)), // CONS
        0b0000_0101 => Some(d3(0b101)), // CAR
        0b0000_0110 => Some(d3(0b110)), // CDR
        0b0000_0011 => Some(d3(0b111)), // EQ
        0b0000_1000 => Some(d4(0b0010)), // LAMBDA
        0b0000_1001 => Some(d4(0b0011)), // DEFINE
        // Existing selector surfaces project explicitly to their ratified D4
        // identities. This is semantic-role mapping, never byte truncation.
        0b0011_0011 => Some(d4(0b1010)), // CAAR
        0b0011_0100 => Some(d4(0b1011)), // CADR
        0b0011_0101 => Some(d4(0b1101)), // CDDR

        // Explicit one-way compatibility delegation for Lisp-owned D5 list
        // and search roles. The historical byte selects only a known role;
        // canonical identity remains the ratified D5 coordinate.
        0b0010_1001 => Some(d5(0b10000)), // APPEND
        0b0010_1010 => Some(d5(0b10001)), // REVERSE
        0b0010_1100 => Some(d5(0b11101)), // MEMBER
        0b0010_1101 => Some(d5(0b11100)), // ASSOC
        _ => None,
    }
}

/// Canonical callable lookup from the exact-domain surface projection.
///
/// Surface -> exact DomainIdentity happens without any historical byte.
/// The Core projection is a downstream callable-boundary decision.
pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    crate::domain_surface_registry::core_identity_for_surface(name)
}
pub(crate) fn semantic_id_bits(semantic_id: SemanticId) -> String {
    semantic_id.to_string()
}

fn live_rows() -> &'static [SemanticRow] {
    SEMANTIC_ROWS
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
        let d3_011 = domain_identity_for_surface("за-умовою").unwrap();
        let d3_111 = domain_identity_for_surface("тотожне?").unwrap();
        let d4_0010 = domain_identity_for_surface("функція").unwrap();
        let d4_0011 = domain_identity_for_surface("визначити").unwrap();

        assert_eq!((d3_011.width(), d3_011.packed_bits()), (3, 0b011));
        assert_eq!((d3_111.width(), d3_111.packed_bits()), (3, 0b111));
        assert_eq!((d4_0010.width(), d4_0010.packed_bits()), (4, 0b0010));
        assert_eq!((d4_0011.width(), d4_0011.packed_bits()), (4, 0b0011));

        assert_ne!(d3_011.packed_bits(), 0b111);
        assert_ne!(d3_111.packed_bits(), 0b011);
        assert_ne!(d4_0010.packed_bits(), 0b1000);
        assert_ne!(d4_0011.packed_bits(), 0b1001);
    }

    #[test]
    fn existing_selector_surfaces_project_to_ratified_d4() {
        for (surface, bits) in [("перше-від-першого", 0b1010), ("перше-від-решти", 0b1011), ("решта-від-решти", 0b1101)] {
            let identity = domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("selector surface must project: {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (4, bits));
        }
        assert_eq!(domain_identity_for_surface("решта-від-першого"), None);
    }

    #[test]
    fn migrated_d5_surface_projects_directly_to_exact_domain_identity() {
        let plus = domain_identity_for_surface("+").expect("plus exact D5 identity");
        assert_eq!((plus.width(), plus.packed_bits()), (5, 0b01010));
    }

    #[test]
    fn canonical_surface_lookup_is_independent_of_legacy_byte_projection() {
        let cond = domain_identity_for_surface("за-умовою").expect("D3 cond identity");
        let define = domain_identity_for_surface("функція").expect("D4 lambda identity");
        assert_eq!((cond.width(), cond.packed_bits()), (3, 0b011));
        assert_eq!((define.width(), define.packed_bits()), (4, 0b0010));

        // A historical registry byte may still delegate one-way to an already
        // known canonical role, but canonical lookup above never depends on it.
        assert_eq!(
            legacy_domain_identity_from_registry_byte(0b0000_0111),
            Some(cond)
        );
        assert_eq!(
            legacy_domain_identity_from_registry_byte(0b0000_1000),
            Some(define)
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
