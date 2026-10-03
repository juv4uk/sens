//! Canonical callable-domain registry.
//!
//! Generated migration snapshot from the ratified exact-width D3/D4 corpus and
//! the full D5/D6 owner maps. Historical 8-bit registry rows are consulted only
//! to project already-existing surface spellings and temporary backend mechanisms.
//! They do not define domain identity or occupancy.

use crate::{Bija3, Bit3, Bit4, Bit5, Bit6, CoreD4, CoreD5, CoreD6, CoreDomainIdentity};

#[derive(Clone, Copy, Debug)]
pub(crate) struct DomainOwnerRow {
    pub width: u8,
    pub bits: u8,
    // Generated diagnostic/provenance metadata. Runtime selection deliberately
    // does not depend on these human-facing fields.
    #[allow(dead_code)]
    pub name: &'static str,
    #[allow(dead_code)]
    pub authority: &'static str,
    pub legacy_mechanism: Option<u8>,
    pub surfaces: &'static [&'static str],
}

include!("domain_registry_generated.rs");

pub(crate) fn identity(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    match width {
        3 => Some(Bija3::from_word(Bit3::new(bits)?).into()),
        4 => Some(CoreD4::from_word(Bit4::new(bits)?).into()),
        5 => Some(CoreD5::from_word(Bit5::new(bits)?).into()),
        6 => Some(CoreD6::from_word(Bit6::new(bits)?).into()),
        _ => None,
    }
}

pub(crate) fn identity_for_surface(surface: &str) -> Option<CoreDomainIdentity> {
    DOMAIN_OWNER_ROWS
        .iter()
        .find(|row| row.surfaces.contains(&surface))
        .and_then(|row| identity(row.width, row.bits))
}

pub(crate) fn row_for_identity(identity_key: CoreDomainIdentity) -> Option<&'static DomainOwnerRow> {
    DOMAIN_OWNER_ROWS.iter().find(|row| {
        identity(row.width, row.bits).is_some_and(|candidate| candidate == identity_key)
    })
}

pub(crate) fn legacy_mechanism_for(identity_key: CoreDomainIdentity) -> Option<u8> {
    row_for_identity(identity_key).and_then(|row| row.legacy_mechanism)
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_ratified_callable_owner_coordinates_are_unique() {
        assert_eq!(DOMAIN_OWNER_ROWS.len(), 117);
        assert_eq!(DOMAIN_OWNER_ROWS.iter().filter(|row| row.width == 3).count(), 7);
        assert_eq!(DOMAIN_OWNER_ROWS.iter().filter(|row| row.width == 4).count(), 14);
        assert_eq!(DOMAIN_OWNER_ROWS.iter().filter(|row| row.width == 5).count(), 32);
        assert_eq!(DOMAIN_OWNER_ROWS.iter().filter(|row| row.width == 6).count(), 64);
        let mut seen = std::collections::HashSet::new();
        for row in DOMAIN_OWNER_ROWS {
            assert!(seen.insert((row.width, row.bits)), "duplicate D{} {:b}", row.width, row.bits);
            assert!(identity(row.width, row.bits).is_some());
        }
    }

    #[test]
    fn generated_owner_projection_keeps_residency_independent_of_legacy_rows() {
        let cdar = DOMAIN_OWNER_ROWS.iter().find(|row| row.width == 4 && row.bits == 0b1100).unwrap();
        assert_eq!(cdar.name, "CDAR");
        assert_eq!(cdar.authority, "exact-width-admitted-corpus");
        assert_eq!(cdar.legacy_mechanism, None);
        assert!(cdar.surfaces.is_empty());

        let plus = DOMAIN_OWNER_ROWS.iter().find(|row| row.width == 5 && row.bits == 0b01010).unwrap();
        assert_eq!(plus.name, "PLUS");
        assert_eq!(plus.authority, "OD-005");
        assert!(plus.surfaces.contains(&"+"));
        assert!(plus.surfaces.contains(&"додати"));
    }

    #[test]
    fn migrated_surfaces_resolve_domain_first() {
        for surface in ["atom?", "eq?", "car", "lambda", "plus", "+", "let", "maplist"] {
            assert!(identity_for_surface(surface).is_some(), "{surface}");
        }
    }

    #[test]
    fn equal_payloads_in_different_domains_never_alias() {
        let d3 = identity(3, 1).unwrap();
        let d4 = identity(4, 1).unwrap();
        let d5 = identity(5, 1).unwrap();
        let d6 = identity(6, 1).unwrap();
        assert_ne!(d3, d4);
        assert_ne!(d4, d5);
        assert_ne!(d5, d6);
    }
}
