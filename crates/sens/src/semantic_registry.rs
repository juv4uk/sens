//! Runtime projection of the Lisp-owned semantic registry.
//!
//! The canonical authority is lib/surface/semantic-registry.lisp and its
//! Lisp-owned reader/API. This module contains no parser for canonical source
//! text. The generated table is emitted by
//! scripts/generate-rust-semantic-registry.lisp and is only a mechanical
//! runtime projection for fast lookup.
//
//! Generated rows still carry the historical flat byte axis as compatibility
//! metadata. Byte-facing APIs in this module are named `legacy_registry_*`;
 //! canonical runtime identity is `CoreDomainIdentity` and is resolved before
//! evaluator/lowering semantics consume the row.

use std::{collections::HashMap, sync::OnceLock};

use crate::{Bija3, Bit3, Bit4, CoreD4, CoreDomainIdentity};
use crate::Sens8;

mod generated {
    include!("semantic_registry_generated.rs");
}

use generated::{SemanticRow, SEMANTIC_ROWS};

pub(crate) type LegacyRegistryId = Sens8;

pub(crate) fn domain_identity_from_registry_byte(byte: u8) -> Option<CoreDomainIdentity> {
    let d3 = |raw| CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()));
    let d4 = |raw| CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()));
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
        // Historical registry coordinates for already-defined selector
        // surfaces project explicitly to their ratified D4 selector identities.
        // This is a role mapping, not byte truncation or nibble inference.
        0b0011_0011 => Some(d4(0b1010)), // CAAR
        0b0011_0100 => Some(d4(0b1011)), // CADR
        0b0011_0101 => Some(d4(0b1101)), // CDDR
        _ => None,
    }
}

pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    registry_byte_for_surface(name).and_then(domain_identity_from_registry_byte)
}
pub(crate) fn legacy_registry_id_bits(legacy_registry_id: LegacyRegistryId) -> String {
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


pub(crate) fn legacy_registry_ids() -> Vec<LegacyRegistryId> {
    live_rows()
        .iter()
        .map(|row| Sens8::from_packed_byte(row.semantic_id))
        .collect()
}

fn insert_surface_mapping(
    index: &mut HashMap<&'static str, LegacyRegistryId>,
    surface: &'static str,
    legacy_registry_id: LegacyRegistryId,
) {
    if let Some(previous) = index.insert(surface, semantic_id) {
        if previous != semantic_id {
            panic!(
                "generated semantic registry surface must be unique: {surface} maps to both {} and {}",
                legacy_registry_id_bits(previous),
                legacy_registry_id_bits(legacy_registry_id)
            );
        }
    }
}

fn surface_index() -> &'static HashMap<&'static str, LegacyRegistryId> {
    static INDEX: OnceLock<HashMap<&'static str, LegacyRegistryId>> = OnceLock::new();
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

pub(crate) fn legacy_registry_id_for_surface(name: &str) -> Option<LegacyRegistryId> {
    surface_index().get(name).copied()
}

fn stable_surfaces_from_legacy_index(
    index: &HashMap<&'static str, LegacyRegistryId>,
    legacy_registry_id: LegacyRegistryId,
) -> Vec<&'static str> {
    let mut surfaces = index
        .iter()
        .filter_map(|(surface, mapped_id)| (*mapped_id == legacy_registry_id).then_some(*surface))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

fn admitted_surfaces_from_legacy_rows(
    rows: &[SemanticRow],
    legacy_registry_id: LegacyRegistryId,
) -> Vec<&'static str> {
    let mut surfaces = rows
        .iter()
        .find(|row| row.semantic_id == legacy_registry_id.packed_byte())
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|surface| surface.name))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

pub(crate) fn stable_surfaces_for_legacy_registry_id(
    legacy_registry_id: LegacyRegistryId,
) -> Vec<&'static str> {
    stable_surfaces_from_legacy_index(surface_index(), semantic_id)
}

pub(crate) fn admitted_surfaces_for_legacy_registry_id(
    legacy_registry_id: LegacyRegistryId,
) -> Vec<&'static str> {
    admitted_surfaces_from_legacy_rows(live_rows(), semantic_id)
}

pub(crate) fn admitted_surfaces_with_namespace_for_legacy_registry_id(
    legacy_registry_id: LegacyRegistryId,
) -> Vec<(&'static str, &'static str)> {
    let mut surfaces = live_rows()
        .iter()
        .find(|row| row.semantic_id == legacy_registry_id.packed_byte())
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
        let cond = domain_identity_for_surface("cond").unwrap();
        let eq = domain_identity_for_surface("eq?").unwrap();
        let lambda = domain_identity_for_surface("lambda").unwrap();
        let define = domain_identity_for_surface("define").unwrap();

        assert_eq!((cond.width(), cond.packed_bits()), (3, 0b011));
        assert_eq!((eq.width(), eq.packed_bits()), (3, 0b111));
        assert_eq!((lambda.width(), lambda.packed_bits()), (4, 0b0010));
        assert_eq!((define.width(), define.packed_bits()), (4, 0b0011));

        assert_ne!(cond.packed_bits(), 0b111);
        assert_ne!(eq.packed_bits(), 0b011);
        assert_ne!(lambda.packed_bits(), 0b1000);
        assert_ne!(define.packed_bits(), 0b1001);
    }

    #[test]
    fn ratified_d4_selector_surfaces_use_exact_domain_identities() {
        for (surface, bits) in [("caar", 0b1010), ("cadr", 0b1011), ("cddr", 0b1101)] {
            let identity = domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("{surface} must have a D4 identity"));
            assert_eq!((identity.width(), identity.packed_bits()), (4, bits));
        }

        // CDAR is ratified as D4:1100, but there is no current legacy registry
        // surface/definition to project. Absence must not mint one from width.
        assert_eq!(domain_identity_for_surface("cdar"), None);
    }

    #[test]
    fn unmigrated_registry_rows_have_no_fake_domain_identity() {
        assert_eq!(domain_identity_for_surface("+"), None);
    }

    #[test]
    fn canonical_domain_lookup_uses_registry_byte_without_sens8_round_trip() {
        assert_eq!(
            registry_byte_for_surface("cond").and_then(domain_identity_from_registry_byte),
            domain_identity_for_surface("cond")
        );
        assert_eq!(
            registry_byte_for_surface("lambda").and_then(domain_identity_from_registry_byte),
            domain_identity_for_surface("lambda")
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
        assert_eq!(legacy_registry_id_for_surface("00001010"), None);
        assert_eq!(legacy_registry_id_for_surface("10101000"), None);
    }

    #[test]
    fn public_reverse_projection_preserves_identity() {
        for surface in admitted_surfaces_for_legacy_registry_id(crate::sens!(00001111)) {
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
        assert_eq!(legacy_registry_id_for_surface("+"), Some(crate::sens!(00001100)));
    }

    #[test]
    fn surfaces_with_namespace_align_with_present_names_and_keep_namespace() {
        let with_namespace = admitted_surfaces_with_namespace_for_legacy_registry_id(crate::sens!(00000001));
        let names_only = admitted_surfaces_for_legacy_registry_id(crate::sens!(00000001));
        assert_eq!(with_namespace.len(), names_only.len());
        assert!(with_namespace.contains(&("en", "quote")));
        assert!(with_namespace.contains(&("ук", "як-є")));
        assert!(with_namespace.contains(&("sym", "'")));
    }
}
