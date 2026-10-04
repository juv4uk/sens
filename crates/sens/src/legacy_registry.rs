//! Historical flat-byte compatibility registry.
//!
//! This module owns the old `SEMANTIC_ROWS[256]` / `Sens8` projection.
//! It is compatibility metadata only. Canonical Core identity, occupancy and
//! callability live outside this module and may never be inferred by numeric
//! truncation/extension of these bytes.

use std::{collections::HashMap, sync::OnceLock};

use crate::Sens8;

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

}
