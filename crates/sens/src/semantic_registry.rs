//! Runtime surface/compatibility projection.
//!
//! Canonical Core semantic identity is domain-qualified and is admitted by the
//! ratified domain laws. The historical flat surface table may donate spellings
//! and legacy compatibility coordinates, but it does not mint Core identity.
//!
//! The generated flat table is emitted by
//! scripts/generate-rust-semantic-registry.lisp. Its packed byte is historical
//! projection metadata only; canonical D3/D4 lookup below declares the domain
//! identity first and consults a legacy row only for its spellings.

use std::{collections::HashMap, sync::OnceLock};

use crate::{Bija3, Bit3, Bit4, CoreD4, CoreDomainIdentity};
use crate::Sens8;

mod generated {
    include!("semantic_registry_generated.rs");
}

use generated::{SemanticRow, SEMANTIC_ROWS};

pub(crate) type SemanticId = Sens8;

#[derive(Clone, Copy)]
struct CanonicalSurfaceProjection {
    identity: CoreDomainIdentity,
    /// Historical flat row used only as a spelling donor.
    ///
    /// This byte is never converted into the canonical identity.
    legacy_surface_row: u8,
}

fn d3(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D3(Bija3::from_word(
        Bit3::new(raw).expect("canonical D3 projection must fit"),
    ))
}

fn d4(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D4(CoreD4::from_word(
        Bit4::new(raw).expect("canonical D4 projection must fit"),
    ))
}

fn canonical_surface_projections() -> [CanonicalSurfaceProjection; 9] {
    [
        CanonicalSurfaceProjection { identity: d3(0b001), legacy_surface_row: 0b0000_0001 }, // QUOTE
        CanonicalSurfaceProjection { identity: d3(0b010), legacy_surface_row: 0b0000_0010 }, // ATOM
        CanonicalSurfaceProjection { identity: d3(0b011), legacy_surface_row: 0b0000_0111 }, // COND
        CanonicalSurfaceProjection { identity: d3(0b100), legacy_surface_row: 0b0000_0100 }, // CONS
        CanonicalSurfaceProjection { identity: d3(0b101), legacy_surface_row: 0b0000_0101 }, // CAR
        CanonicalSurfaceProjection { identity: d3(0b110), legacy_surface_row: 0b0000_0110 }, // CDR
        CanonicalSurfaceProjection { identity: d3(0b111), legacy_surface_row: 0b0000_0011 }, // EQ
        CanonicalSurfaceProjection { identity: d4(0b0010), legacy_surface_row: 0b0000_1000 }, // LAMBDA
        CanonicalSurfaceProjection { identity: d4(0b0011), legacy_surface_row: 0b0000_1001 }, // DEFINE
    ]
}

fn legacy_row(byte: u8) -> Option<&'static SemanticRow> {
    live_rows().iter().find(|row| row.semantic_id == byte)
}

pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    canonical_surface_projections()
        .into_iter()
        .find_map(|projection| {
            let row = legacy_row(projection.legacy_surface_row)?;
            row.surfaces
                .iter()
                .any(|surface| surface.name == name)
                .then_some(projection.identity)
        })
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
    fn canonical_domain_lookup_declares_identity_before_legacy_spelling_projection() {
        let cond = canonical_surface_projections()
            .into_iter()
            .find(|projection| projection.identity == d3(0b011))
            .expect("COND must have a canonical projection");
        let lambda = canonical_surface_projections()
            .into_iter()
            .find(|projection| projection.identity == d4(0b0010))
            .expect("LAMBDA must have a canonical projection");

        assert_eq!(cond.legacy_surface_row, 0b0000_0111);
        assert_eq!(lambda.legacy_surface_row, 0b0000_1000);

        assert_eq!(domain_identity_for_surface("за-умовою"), Some(d3(0b011)));
        assert_eq!(domain_identity_for_surface("функція"), Some(d4(0b0010)));

        // Historical byte payload and canonical exact-domain payload are
        // deliberately different facts. The row donates spelling only.
        assert_ne!(cond.legacy_surface_row, cond.identity.packed_bits());
        assert_ne!(lambda.legacy_surface_row, lambda.identity.packed_bits());
    }

    #[test]
    fn legacy_generated_registry_is_one_contiguous_byte_axis_only() {
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
