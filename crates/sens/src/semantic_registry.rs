//! Canonical exact-domain registry projection.
//!
//! Occupancy authority is the generated 510/510 D1-D8 projection from #3029.
//! Human surfaces are optional projections from knowledge/domain-surface-registry.lisp.
//! Neither surface presence nor callability can create or erase a domain resident.
//! Historical flat Sens8 metadata lives only in legacy_registry.rs.

use std::{
    collections::{HashMap, HashSet},
    sync::OnceLock,
};

use crate::{
    domain_owner_generated::DOMAIN_OWNER_COORDINATES, BinarySourceWord, Bit1, Bit2, Bit3, Bit4,
    Bit5, Bit6, Bit7, Bit8, DomainIdentity,
};

mod generated {
    include!("domain_surface_registry_generated.rs");
}

use generated::DOMAIN_SURFACE_ROWS;

pub(crate) fn exact_domain_identity(width: u8, bits: u8) -> Option<DomainIdentity> {
    let source = match width {
        1 => BinarySourceWord::W1(Bit1::new(bits)?),
        2 => BinarySourceWord::W2(Bit2::new(bits)?),
        3 => BinarySourceWord::W3(Bit3::new(bits)?),
        4 => BinarySourceWord::W4(Bit4::new(bits)?),
        5 => BinarySourceWord::W5(Bit5::new(bits)?),
        6 => BinarySourceWord::W6(Bit6::new(bits)?),
        7 => BinarySourceWord::W7(Bit7::new(bits)?),
        8 => BinarySourceWord::W8(Bit8::new(bits)?),
        _ => return None,
    };
    Some(DomainIdentity::from_source_word(source))
}

fn occupancy() -> &'static HashSet<DomainIdentity> {
    static OCCUPANCY: OnceLock<HashSet<DomainIdentity>> = OnceLock::new();
    OCCUPANCY.get_or_init(|| {
        let set = DOMAIN_OWNER_COORDINATES
            .iter()
            .map(|row| {
                exact_domain_identity(row.width, row.bits).unwrap_or_else(|| {
                    panic!(
                        "generated owner coordinate is not a valid exact domain: D{}:{:b}",
                        row.width, row.bits
                    )
                })
            })
            .collect::<HashSet<_>>();
        assert_eq!(
            set.len(),
            DOMAIN_OWNER_COORDINATES.len(),
            "generated owner occupancy must contain unique exact-domain identities"
        );
        set
    })
}

pub(crate) fn is_occupied(identity: DomainIdentity) -> bool {
    occupancy().contains(&identity)
}

pub(crate) fn occupied_domain_identities() -> Vec<DomainIdentity> {
    DOMAIN_OWNER_COORDINATES
        .iter()
        .map(|row| {
            exact_domain_identity(row.width, row.bits)
                .expect("generated owner coordinate must be exact D1-D8 identity")
        })
        .collect()
}

fn surface_index() -> &'static HashMap<&'static str, DomainIdentity> {
    static INDEX: OnceLock<HashMap<&'static str, DomainIdentity>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in DOMAIN_SURFACE_ROWS {
            let identity = exact_domain_identity(row.width, row.bits).unwrap_or_else(|| {
                panic!(
                    "generated surface row is not a valid exact domain: D{}:{:b}",
                    row.width, row.bits
                )
            });
            assert!(
                is_occupied(identity),
                "surface projection may only name an owner-ratified resident: D{}:{:0width$b}",
                identity.width(),
                identity.packed_bits(),
                width = identity.width()
            );
            for surface in row.surfaces {
                if let Some(previous) = index.insert(surface.name, identity) {
                    assert_eq!(
                        previous, identity,
                        "one surface may not project to two exact-domain identities: {}",
                        surface.name
                    );
                }
            }
        }
        index
    })
}

/// Resolve an admitted human/symbolic spelling to an already-existing exact-domain identity.
///
/// Surface presence is projection-only. It grants neither occupancy nor callability.
pub(crate) fn domain_identity_for_surface(name: &str) -> Option<DomainIdentity> {
    surface_index().get(name).copied()
}

pub(crate) fn domain_surface_bindings() -> Vec<(&'static str, DomainIdentity)> {
    let mut bindings = DOMAIN_SURFACE_ROWS
        .iter()
        .filter_map(|row| {
            exact_domain_identity(row.width, row.bits)
                .filter(|identity| is_occupied(*identity))
                .map(|identity| (identity, row.surfaces))
        })
        .flat_map(|(identity, surfaces)| {
            surfaces.iter().map(move |surface| (surface.name, identity))
        })
        .collect::<Vec<_>>();
    bindings.sort_unstable_by(|left, right| left.0.cmp(right.0));
    bindings.dedup();
    bindings
}

pub(crate) fn surfaces_for_domain_identity(identity: DomainIdentity) -> Vec<&'static str> {
    if !is_occupied(identity) {
        return Vec::new();
    }
    let mut surfaces = DOMAIN_SURFACE_ROWS
        .iter()
        .filter(|row| exact_domain_identity(row.width, row.bits) == Some(identity))
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
    fn owner_occupancy_is_full_d1_d8_and_surface_independent() {
        let occupied = occupied_domain_identities();
        assert_eq!(occupied.len(), 510);

        for (width, expected) in [
            (1usize, 2usize),
            (2, 4),
            (3, 8),
            (4, 16),
            (5, 32),
            (6, 64),
            (7, 128),
            (8, 256),
        ] {
            assert_eq!(
                occupied.iter().filter(|identity| identity.width() == width).count(),
                expected
            );
        }

        let d7_zero = exact_domain_identity(7, 0).unwrap();
        let d8_zero = exact_domain_identity(8, 0).unwrap();
        assert!(is_occupied(d7_zero));
        assert!(is_occupied(d8_zero));
        assert!(surfaces_for_domain_identity(d7_zero).is_empty());
        assert!(surfaces_for_domain_identity(d8_zero).is_empty());
    }

    #[test]
    fn equal_payloads_remain_distinct_across_domains() {
        let d3 = exact_domain_identity(3, 1).unwrap();
        let d4 = exact_domain_identity(4, 1).unwrap();
        let d7 = exact_domain_identity(7, 1).unwrap();
        let d8 = exact_domain_identity(8, 1).unwrap();
        assert_ne!(d3, d4);
        assert_ne!(d4, d7);
        assert_ne!(d7, d8);
        assert!(is_occupied(d3) && is_occupied(d4) && is_occupied(d7) && is_occupied(d8));
    }

    #[test]
    fn surfaced_rows_project_to_existing_exact_domain_identity() {
        for (surface, width, bits) in [
            ("за-умовою", 3usize, 0b011u8),
            ("функція", 4, 0b0010),
            ("перше-від-решти", 4, 0b1011),
            ("+", 5, 0b01010),
        ] {
            let identity = domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("missing exact-domain surface {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (width, bits));
            assert!(is_occupied(identity));
        }
    }

    #[test]
    fn lisp_owned_d5_surfaces_are_exact_domain_projection() {
        for (surface, bits) in [
            ("append", 0b10000),
            ("reverse", 0b10001),
            ("assoc", 0b11100),
            ("member?", 0b11101),
            ("subst", 0b11111),
        ] {
            let identity = domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("missing exact D5 projection for {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (5, bits));
            assert!(is_occupied(identity));
        }
    }

    #[test]
    fn historical_surface_absence_cannot_mint_or_delete_occupancy() {
        assert_eq!(domain_identity_for_surface("корінь"), None);
        assert!(is_occupied(exact_domain_identity(8, 0b1111_1111).unwrap()));
    }
}
