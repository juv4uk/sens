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

use crate::{Bija3, Bit3, Bit4, CallableDomainId, CoreD4, LegacySens8, Sens8};

mod generated {
    include!("semantic_registry_generated.rs");
}

use generated::{SemanticRow, SEMANTIC_ROWS};

pub(crate) type SemanticId = Sens8;

pub(crate) type DomainSemanticId = CallableDomainId;

/// Role-aware migration from the historical generated registry byte axis.
///
/// This is intentionally not a truncation/zero-extension rule.  The D3
/// EQ/COND swap is the negative witness: legacy 00000011 -> D3 111 while
/// legacy 00000111 -> D3 011.  D4 LAMBDA/DEFINE likewise use their ratified
/// bootstrap coordinates rather than low nibbles.
///
/// Rows not yet migrated remain explicitly Legacy8 until their D5/D6 owner-map
/// slice is wired in.
pub(crate) fn domain_semantic_id_from_registry_byte(byte: u8) -> DomainSemanticId {
    let d3 = |raw| {
        CallableDomainId::D3(Bija3::from_word(
            Bit3::new(raw).expect("constant D3 coordinate must fit"),
        ))
    };
    let d4 = |raw| {
        CallableDomainId::D4(CoreD4::from_word(
            Bit4::new(raw).expect("constant D4 coordinate must fit"),
        ))
    };

    match byte {
        0b0000_0001 => d3(0b001), // QUOTE
        0b0000_0010 => d3(0b010), // ATOM
        0b0000_0111 => d3(0b011), // COND
        0b0000_0100 => d3(0b100), // CONS
        0b0000_0101 => d3(0b101), // CAR
        0b0000_0110 => d3(0b110), // CDR
        0b0000_0011 => d3(0b111), // EQ
        0b0000_1000 => d4(0b0010), // LAMBDA
        0b0000_1001 => d4(0b0011), // DEFINE
        other => CallableDomainId::from_legacy(LegacySens8::from_packed_byte(other)),
    }
}

/// Compatibility reverse edge used only to index the still-byte-shaped
/// generated projection. Exact-domain identity remains canonical.
pub(crate) fn registry_byte_for_domain_semantic_id(id: DomainSemanticId) -> u8 {
    match id {
        CallableDomainId::D3(word) => match word.word().packed_bits() {
            0b001 => 0b0000_0001, // QUOTE
            0b010 => 0b0000_0010, // ATOM
            0b011 => 0b0000_0111, // COND
            0b100 => 0b0000_0100, // CONS
            0b101 => 0b0000_0101, // CAR
            0b110 => 0b0000_0110, // CDR
            0b111 => 0b0000_0011, // EQ
            other => panic!("unmapped D3 registry coordinate {other:03b}"),
        },
        CallableDomainId::D4(word) => match word.word().packed_bits() {
            0b0010 => 0b0000_1000, // LAMBDA
            0b0011 => 0b0000_1001, // DEFINE
            other => panic!("D4 coordinate {other:04b} is not migrated into registry yet"),
        },
        CallableDomainId::Legacy8(word) => word.packed_byte(),
        CallableDomainId::D5(_) | CallableDomainId::D6(_) => {
            panic!("D5/D6 registry reverse map must come from owner-map migration")
        }
    }
}

pub(crate) fn admitted_domain_semantic_ids() -> Vec<DomainSemanticId> {
    live_rows()
        .iter()
        .map(|row| domain_semantic_id_from_registry_byte(row.semantic_id))
        .collect()
}

pub(crate) fn admitted_domain_semantic_id_for_surface(name: &str) -> Option<DomainSemanticId> {
    admitted_semantic_id_for_surface(name)
        .map(|legacy| domain_semantic_id_from_registry_byte(legacy.packed_byte()))
}

pub(crate) fn domain_semantic_id_for_surface(name: &str) -> Option<DomainSemanticId> {
    admitted_domain_semantic_id_for_surface(name)
}

pub(crate) fn stable_surfaces_for_domain_semantic_id(
    semantic_id: DomainSemanticId,
) -> Vec<&'static str> {
    stable_surfaces_for_semantic_id(Sens8::from_packed_byte(
        registry_byte_for_domain_semantic_id(semantic_id),
    ))
}

pub(crate) fn admitted_surfaces_for_domain_semantic_id(
    semantic_id: DomainSemanticId,
) -> Vec<&'static str> {
    admitted_surfaces_for_semantic_id(Sens8::from_packed_byte(
        registry_byte_for_domain_semantic_id(semantic_id),
    ))
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
    fn domain_projection_is_role_aware_not_bit_truncation() {
        let cond = domain_semantic_id_for_surface("cond").expect("COND surface");
        let eq = domain_semantic_id_for_surface("eq").expect("EQ surface");
        let lambda = domain_semantic_id_for_surface("lambda").expect("LAMBDA surface");
        let define = domain_semantic_id_for_surface("define").expect("DEFINE surface");

        assert_eq!(cond.width(), 3);
        assert_eq!(cond.packed_bits(), 0b011);
        assert_eq!(eq.width(), 3);
        assert_eq!(eq.packed_bits(), 0b111);
        assert_eq!(lambda.width(), 4);
        assert_eq!(lambda.packed_bits(), 0b0010);
        assert_eq!(define.width(), 4);
        assert_eq!(define.packed_bits(), 0b0011);

        // Explicit falsifiers for zero-padding / low-nibble migration.
        assert_ne!(cond.packed_bits(), 0b111);
        assert_ne!(eq.packed_bits(), 0b011);
        assert_ne!(lambda.packed_bits(), 0b1000);
        assert_ne!(define.packed_bits(), 0b1001);
    }

    #[test]
    fn unmigrated_registry_rows_are_explicit_legacy_only() {
        let plus = domain_semantic_id_for_surface("+").expect("+ surface");
        assert_eq!(plus.width(), 8);
        assert!(plus.legacy().is_some());
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
