//! Canonical human/symbol surface projection onto exact D1-D8 identities.
//!
//! This module is deliberately separate from the historical flat-256 registry.
//! A surface may only name an already-occupied CURRENT D1-D8 coordinate.
//! Occupancy comes from #3029/#3064; surfaces never mint residency, role,
//! callability, law, or runtime mechanism.

use std::{collections::HashMap, sync::OnceLock};

use crate::{
    domain_owner_generated::DOMAIN_OWNER_COORDINATES, Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7,
    Bit8, BinarySourceWord, CoreDomainIdentity, DomainIdentity,
};

mod generated {
    include!("domain_surface_registry_generated.rs");
}

use generated::DOMAIN_SURFACE_ROWS;

fn exact_source_word(width: u8, bits: u8) -> Option<BinarySourceWord> {
    Some(match width {
        1 => BinarySourceWord::W1(Bit1::new(bits)?),
        2 => BinarySourceWord::W2(Bit2::new(bits)?),
        3 => BinarySourceWord::W3(Bit3::new(bits)?),
        4 => BinarySourceWord::W4(Bit4::new(bits)?),
        5 => BinarySourceWord::W5(Bit5::new(bits)?),
        6 => BinarySourceWord::W6(Bit6::new(bits)?),
        7 => BinarySourceWord::W7(Bit7::new(bits)?),
        8 => BinarySourceWord::W8(Bit8::new(bits)?),
        _ => return None,
    })
}

fn current_coordinate_is_occupied(width: u8, bits: u8) -> bool {
    if !crate::domain_owner_generated::DOMAIN_WIDTHS_IN_SCOPE.contains(&width) {
        return false;
    }
    DOMAIN_OWNER_COORDINATES
        .iter()
        .any(|row| row.width == width && row.bits == bits)
}

/// Lift one exact CURRENT coordinate into universal D1-D8 identity.
///
/// This does not assert role/callability. It only proves that the row is a
/// valid bounded exact-width word and is occupied by owner ratification.
pub(crate) fn identity_for_coordinate(width: u8, bits: u8) -> Option<DomainIdentity> {
    if !current_coordinate_is_occupied(width, bits) {
        return None;
    }
    exact_source_word(width, bits).map(DomainIdentity::from_source_word)
}

fn surface_index() -> &'static HashMap<&'static str, DomainIdentity> {
    static INDEX: OnceLock<HashMap<&'static str, DomainIdentity>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in DOMAIN_SURFACE_ROWS {
            let identity = identity_for_coordinate(row.width, row.bits).unwrap_or_else(|| {
                panic!(
                    "surface projection references non-occupied CURRENT coordinate: D{} {:b}",
                    row.width, row.bits
                )
            });

            for surface in row.surfaces {
                if let Some(previous) = index.insert(surface.name, identity) {
                    assert_eq!(
                        previous, identity,
                        "surface must not map to two exact-domain identities: {}",
                        surface.name
                    );
                }
            }
        }
        index
    })
}

/// Resolve one admitted human/symbol spelling directly to universal exact
/// domain identity. No Sens8/Function8 byte participates.
pub(crate) fn identity_for_surface(name: &str) -> Option<DomainIdentity> {
    surface_index().get(name).copied()
}

/// Callable projection for the existing evaluator boundary.
///
/// This is intentionally downstream of universal DomainIdentity: a surface
/// does not become callable merely because it exists. D1/D2/D7 therefore fail
/// closed here.
pub(crate) fn core_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    identity_for_surface(name)?.core_operation()
}

/// First-class projection for consumers that need spelling + exact identity.
#[allow(dead_code)]
pub(crate) fn bindings() -> Vec<(&'static str, DomainIdentity)> {
    let mut bindings = surface_index()
        .iter()
        .map(|(surface, identity)| (*surface, *identity))
        .collect::<Vec<_>>();
    bindings.sort_unstable_by(|left, right| left.0.cmp(right.0));
    bindings
}

/// Reverse projection for presentation/tooling only.
#[allow(dead_code)]
pub(crate) fn surfaces_for_identity(identity: DomainIdentity) -> Vec<&'static str> {
    let mut surfaces = DOMAIN_SURFACE_ROWS
        .iter()
        .filter(|row| identity_for_coordinate(row.width, row.bits) == Some(identity))
        .flat_map(|row| row.surfaces.iter().map(|surface| surface.name))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces.dedup();
    surfaces
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn surface_projection_is_direct_exact_domain_not_legacy_byte() {
        for (surface, width, bits) in [
            ("car", 3usize, 0b101u8),
            ("lambda", 4, 0b0010),
            ("cadr", 4, 0b1011),
            ("append", 5, 0b10000),
            ("reverse", 5, 0b10001),
            ("assoc", 5, 0b11100),
            ("member?", 5, 0b11101),
        ] {
            let identity = identity_for_surface(surface)
                .unwrap_or_else(|| panic!("missing exact-domain surface: {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (width, bits));
        }
    }

    #[test]
    fn projection_cannot_mint_unoccupied_or_out_of_range_coordinates() {
        assert_eq!(identity_for_coordinate(0, 0), None);
        assert_eq!(identity_for_coordinate(9, 0), None);
        assert_eq!(identity_for_coordinate(3, 0b1000), None);
    }

    #[test]
    fn all_ratified_current_coordinates_are_available_independently_of_surfaces() {
        assert_eq!(DOMAIN_OWNER_COORDINATES.len(), 510);
        assert!(identity_for_coordinate(7, 0b1111111).is_some());
        assert!(identity_for_coordinate(8, 0b11111111).is_some());
        assert_eq!(identity_for_surface("not-a-surface"), None);
    }

    #[test]
    fn d7_and_d8_occupancy_does_not_require_a_surface_or_callable_role() {
        let d7 = identity_for_coordinate(7, 1).expect("D7 current coordinate occupied");
        let d8 = identity_for_coordinate(8, 1).expect("D8 current coordinate occupied");
        assert_eq!((d7.width(), d7.packed_bits()), (7, 1));
        assert_eq!((d8.width(), d8.packed_bits()), (8, 1));
        assert_ne!(d7, d8);
    }

    #[test]
    fn reverse_projection_is_optional_metadata_only() {
        let identity = identity_for_surface("cadr").expect("cadr surface");
        let surfaces = surfaces_for_identity(identity);
        assert!(surfaces.contains(&"cadr"));
    }
}
