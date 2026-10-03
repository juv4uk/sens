//! Historical flat-byte compatibility registry.
//!
//! This module owns the old `SEMANTIC_ROWS[256]` / `Sens8` projection.
//! It is compatibility metadata only. Canonical Core identity, occupancy and
//! callability live outside this module and may never be inferred by numeric
//! truncation/extension of these bytes.

use std::{collections::HashMap, sync::OnceLock};

use crate::{Bija3, Bit3, Bit4, CoreD4, CoreDomainIdentity, Sens8};

mod generated {
    include!("semantic_registry_generated.rs");
}

use generated::{SemanticRow, SEMANTIC_ROWS};

pub(crate) type LegacyRegistryId = Sens8;

pub(crate) fn id_bits(id: LegacyRegistryId) -> String {
    id.to_string()
}

fn rows() -> &'static [SemanticRow] {
    SEMANTIC_ROWS
}

pub(crate) fn admitted_ids() -> Vec<LegacyRegistryId> {
    rows()
        .iter()
        .map(|row| Sens8::from_packed_byte(row.semantic_id))
        .collect()
}

fn insert_surface(
    index: &mut HashMap<&'static str, LegacyRegistryId>,
    surface: &'static str,
    id: LegacyRegistryId,
) {
    if let Some(previous) = index.insert(surface, id) {
        if previous != id {
            panic!(
                "legacy registry surface must be unique: {surface} maps to both {} and {}",
                id_bits(previous),
                id_bits(id)
            );
        }
    }
}

fn surface_index() -> &'static HashMap<&'static str, LegacyRegistryId> {
    static INDEX: OnceLock<HashMap<&'static str, LegacyRegistryId>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in rows() {
            for surface in row.surfaces {
                insert_surface(
                    &mut index,
                    surface.name,
                    Sens8::from_packed_byte(row.semantic_id),
                );
            }
        }
        index
    })
}

pub(crate) fn id_for_surface(name: &str) -> Option<LegacyRegistryId> {
    surface_index().get(name).copied()
}

pub(crate) fn stable_surfaces_for_id(id: LegacyRegistryId) -> Vec<&'static str> {
    let mut surfaces = surface_index()
        .iter()
        .filter_map(|(surface, mapped)| (*mapped == id).then_some(*surface))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

pub(crate) fn admitted_surfaces_for_id(id: LegacyRegistryId) -> Vec<&'static str> {
    let mut surfaces = rows()
        .iter()
        .find(|row| row.semantic_id == id.packed_byte())
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|surface| surface.name))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

pub(crate) fn admitted_surfaces_with_namespace_for_id(
    id: LegacyRegistryId,
) -> Vec<(&'static str, &'static str)> {
    let mut surfaces = rows()
        .iter()
        .find(|row| row.semantic_id == id.packed_byte())
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|surface| (surface.namespace, surface.name)))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

/// Explicit one-way compatibility bridge for historical executable bytes.
///
/// This list exists only so an old byte input can delegate to a mechanism that
/// has already become canonical. The mapping never defines canonical meaning.
pub(crate) fn domain_identity_from_byte(byte: u8) -> Option<CoreDomainIdentity> {
    let d3 = |raw| CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()));
    let d4 = |raw| CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()));

    match byte {
        0b0000_0001 => Some(d3(0b001)),
        0b0000_0010 => Some(d3(0b010)),
        0b0000_0111 => Some(d3(0b011)),
        0b0000_0100 => Some(d3(0b100)),
        0b0000_0101 => Some(d3(0b101)),
        0b0000_0110 => Some(d3(0b110)),
        0b0000_0011 => Some(d3(0b111)),
        0b0000_1000 => Some(d4(0b0010)),
        0b0000_1001 => Some(d4(0b0011)),
        0b0011_0011 => Some(d4(0b1010)),
        0b0011_0100 => Some(d4(0b1011)),
        0b0011_0101 => Some(d4(0b1101)),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use generated::SemanticSurface;

    #[test]
    fn flat_axis_is_explicitly_legacy() {
        assert_eq!(SEMANTIC_ROWS.len(), 256);
        assert_eq!(SEMANTIC_ROWS.first().map(|row| row.semantic_id), Some(0));
        assert_eq!(SEMANTIC_ROWS.last().map(|row| row.semantic_id), Some(255));
    }

    #[test]
    fn legacy_surface_projection_remains_available_for_compatibility() {
        assert_eq!(id_for_surface("+"), Some(crate::sens!(00001100)));
        let surfaces = &SEMANTIC_ROWS[1].surfaces;
        assert!(surfaces.contains(&SemanticSurface { namespace: "ук", name: "як-є" }));
    }

    #[test]
    fn compatibility_bridge_is_role_mapping_not_truncation() {
        let cond = domain_identity_from_byte(0b0000_0111).unwrap();
        let eq = domain_identity_from_byte(0b0000_0011).unwrap();
        assert_eq!((cond.width(), cond.packed_bits()), (3, 0b011));
        assert_eq!((eq.width(), eq.packed_bits()), (3, 0b111));
    }
}
