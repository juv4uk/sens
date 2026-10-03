//! Exact-domain surface projection plus isolated historical compatibility.
//!
//! Canonical migrated surface identity comes from
//! `lib/surface/domain-registry.lisp` -> `domain_surface_registry_generated.rs`
//! and is keyed by exact `CoreDomainIdentity`.
//!
//! The older `semantic-registry.lisp` / `SEMANTIC_ROWS` byte axis remains
//! below only for explicit compatibility consumers that have not migrated yet.
//! It is not an authority for domain identity, occupancy, or callability.

use std::{collections::HashMap, sync::OnceLock};

use crate::{Bija3, Bit3, Bit4, CoreD4, CoreDomainIdentity};
use crate::Sens8;

mod generated {
    include!("semantic_registry_generated.rs");
}

mod domain_generated {
    include!("domain_surface_registry_generated.rs");
}

use generated::{SemanticRow, SEMANTIC_ROWS};
use domain_generated::DOMAIN_SURFACE_ROWS;

pub(crate) type SemanticId = Sens8;

fn domain_identity_from_exact_row(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    match width {
        3 => Bit3::new(bits)
            .map(Bija3::from_word)
            .map(CoreDomainIdentity::D3),
        4 => Bit4::new(bits)
            .map(CoreD4::from_word)
            .map(CoreDomainIdentity::D4),
        _ => None,
    }
}

fn domain_surface_index() -> &'static HashMap<&'static str, CoreDomainIdentity> {
    static INDEX: OnceLock<HashMap<&'static str, CoreDomainIdentity>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in DOMAIN_SURFACE_ROWS {
            let identity = domain_identity_from_exact_row(row.width, row.bits)
                .unwrap_or_else(|| panic!(
                    "generated exact-domain row is unsupported: width={} bits={:b}",
                    row.width, row.bits
                ));
            for surface in row.surfaces {
                if let Some(previous) = index.insert(surface.name, identity) {
                    assert_eq!(
                        previous, identity,
                        "exact-domain surface must not map to two identities: {}",
                        surface.name
                    );
                }
            }
        }
        index
    })
}

/// Canonical migrated surface -> exact-domain identity route.
///
/// This lookup is independent of the historical 256-row byte registry. The
/// flat registry remains available below only for explicit compatibility APIs
/// and unmigrated operations.
pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    domain_surface_index().get(name).copied()
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
    fn unmigrated_registry_rows_have_no_fake_domain_identity() {
        assert_eq!(domain_identity_for_surface("+"), None);
    }

    #[test]
    fn canonical_domain_lookup_uses_exact_domain_projection() {
        for (surface, width, bits) in [
            ("за-умовою", 3, 0b011),
            ("функція", 4, 0b0010),
            ("caar", 4, 0b1010),
            ("cadr", 4, 0b1011),
            ("cddr", 4, 0b1101),
        ] {
            let identity = domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("missing exact-domain surface: {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (width, bits));
        }
    }

    #[test]
    fn legacy_byte_axis_is_not_required_for_canonical_domain_lookup() {
        let cadr_domain = domain_identity_for_surface("cadr").expect("cadr exact-domain route");
        let historical_byte = semantic_id_for_surface("cadr")
            .expect("legacy compatibility row")
            .packed_byte();

        assert_eq!((cadr_domain.width(), cadr_domain.packed_bits()), (4, 0b1011));
        assert_eq!(historical_byte, 0b0011_0100);
        assert_ne!(cadr_domain.packed_bits(), historical_byte);
    }

    #[test]
    fn legacy_generated_registry_is_one_contiguous_byte_axis() {
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
