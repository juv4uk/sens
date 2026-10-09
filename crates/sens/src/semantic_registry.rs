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

use crate::{Bit3, Bit4, Bit5, CoreD5, CoreDomainIdentity, DomainIdentity};
use crate::Sens8;

mod generated {
    include!("semantic_registry_generated.rs");
}

mod domain_surface_generated {
    include!("domain_surface_registry_generated.rs");
}

mod d5_definition_bindings_generated {
    include!("d5_definition_bindings_generated.rs");
}

use d5_definition_bindings_generated::D5_DEFINITION_BINDINGS;
use domain_surface_generated::DOMAIN_SURFACE_ROWS;
use generated::{SemanticRow, SEMANTIC_ROWS};

pub(crate) type SemanticId = Sens8;

fn exact_domain_identity_from_projection(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    // Канонічний маршрут: точне слово драбини → домен → допущений механізм.
    // Ні ширина сама по собі, ні старий байт не створюють callable identity.
    use crate::BinarySourceWord;
    let source = match width {
        3 => BinarySourceWord::W3(Bit3::new(bits)?),
        4 => BinarySourceWord::W4(Bit4::new(bits)?),
        5 => BinarySourceWord::W5(Bit5::new(bits)?),
        6 => BinarySourceWord::W6(crate::Bit6::new(bits)?),
        _ => return None,
    };
    CoreDomainIdentity::from_source_word(source)
}

/// Direct D3/D4/D5 human-surface projection.
///
/// This path consumes the exact-domain projection generated from
/// lib/domains/d1.lisp ... lib/domains/d5.lisp. It never consults a historical
/// packed byte to recover domain identity.
fn direct_domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    DOMAIN_SURFACE_ROWS.iter().find_map(|row| {
        let matches_human_surface = row.source_routable
            && row
                .surfaces
                .iter()
                .any(|surface| matches!(surface.namespace, "uk" | "sa" | "en") && surface.name == name);
        matches_human_surface
            .then(|| exact_domain_identity_from_projection(row.width, row.bits))
            .flatten()
    })
}
 
/// Canonical Ukrainian *source-head* projection, before evaluation.
///
/// Only owner-ratified source-routable uk rows are eligible. This is NOT the
/// legacy SID compatibility index: no en alias, old W8, D2 structure, or
/// unratified D7 binder can become a callable head via this API.
/// The mixed reader applies it only to executable HEAD positions.
pub(crate) fn exact_uk_callable_for_source_head(name: &str) -> Option<crate::DomainIdentity> {
    DOMAIN_SURFACE_ROWS.iter().find_map(|row| {
        if !row.source_routable
            || !row.surfaces.iter().any(|surface|
                surface.namespace == "uk" && surface.name == name)
        {
            return None;
        }
        exact_domain_identity_from_projection(row.width, row.bits)
            .map(crate::DomainIdentity::from)
    })
}


/// Binding-only OD-005 bootstrap projection for Lisp-owned definitions.
///
/// This MUST NOT be used to reinterpret historical Sens8 calls. Its only
/// consumer is `bind_language_definition`: a definition discovered through
/// the compatibility surface registry is bound once into an already-ratified
/// exact D5 slot. #3062 removes this bootstrap detour.
/// Binding-only exact D5 lookup for existing Lisp definitions.
///
/// The table is generated from Lisp-owned projection data and may only supply
/// a mechanism to an identity already ratified by #3305/#3331.
pub(crate) fn d5_binding_identity_for_definition(name: &str) -> Option<CoreDomainIdentity> {
    D5_DEFINITION_BINDINGS
        .iter()
        .find(|row| row.name == name)
        .map(|row| CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(row.bits).unwrap())))
}

/// Канонічний surface → domain маршрут читає тільки ратифіковану
/// exact-width проєкцію. Історичний SID/байт не визначає домен.
pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    direct_domain_identity_for_surface(name)
}

pub(crate) fn surface_for_domain_identity(
    identity: DomainIdentity,
    namespace: &str,
) -> Option<&'static str> {
    DOMAIN_SURFACE_ROWS
        .iter()
        .find(|row| {
            usize::from(row.width) == identity.width()
                && u16::from(row.bits) == identity.packed_bits()
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
mod exact_d5_binding_projection_tests {
    use super::*;

    #[test]
    fn every_generated_d5_definition_uses_its_exact_domain_word() {
        for row in D5_DEFINITION_BINDINGS {
            let identity = d5_binding_identity_for_definition(row.name)
                .expect("generated Lisp-owned D5 binding must resolve");
            assert_eq!(
                identity,
                CoreDomainIdentity::D5(CoreD5::from_word(
                    Bit5::new(row.bits).expect("generated D5 bit width")
                )),
                "the canonical D5 identity must come from the generated ladder row"
            );
        }
    }

    #[test]
    fn unknown_definition_does_not_gain_a_d5_coordinate() {
        assert_eq!(d5_binding_identity_for_definition("__unknown_d5_binding__"), None);
    }
}
