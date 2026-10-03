//! Canonical exact-domain surface registry.
//!
//! Authority: `lib/surface/domain-registry.lisp`.
//! Identity is exact domain + exact bits. This module has no Sens8/Sid8/
//! Function8 table and performs no legacy-byte-to-domain inference.

use std::{collections::HashMap, sync::OnceLock};

use crate::{
    Bija3, Bit3, Bit4, Bit5, Bit6, CoreD4, CoreD5, CoreD6, CoreDomainIdentity,
};

mod generated {
    include!("domain_surface_registry_generated.rs");
}

use generated::DOMAIN_SURFACE_ROWS;

fn identity_from_row(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    match width {
        3 => Bit3::new(bits)
            .map(Bija3::from_word)
            .map(CoreDomainIdentity::D3),
        4 => Bit4::new(bits)
            .map(CoreD4::from_word)
            .map(CoreDomainIdentity::D4),
        5 => Bit5::new(bits)
            .map(CoreD5::from_word)
            .map(CoreDomainIdentity::D5),
        6 => Bit6::new(bits)
            .map(CoreD6::from_word)
            .map(CoreDomainIdentity::D6),
        _ => None,
    }
}

fn surface_index() -> &'static HashMap<&'static str, CoreDomainIdentity> {
    static INDEX: OnceLock<HashMap<&'static str, CoreDomainIdentity>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in DOMAIN_SURFACE_ROWS {
            let identity = identity_from_row(row.width, row.bits).unwrap_or_else(|| {
                panic!(
                    "generated exact-domain row is unsupported: width={} bits={:b}",
                    row.width, row.bits
                )
            });
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

/// Resolve one admitted human surface to its already-known exact domain identity.
///
/// Surface spelling is a projection only: rows cannot create occupancy or
/// callability, and there is no fallback through the historical byte table.
pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    surface_index().get(name).copied()
}

/// Reverse projection for UI/tooling over already-known exact identity.
pub(crate) fn surfaces_for_identity(identity: CoreDomainIdentity) -> Vec<&'static str> {
    let mut surfaces = DOMAIN_SURFACE_ROWS
        .iter()
        .filter_map(|row| {
            (identity_from_row(row.width, row.bits) == Some(identity)).then_some(row.surfaces)
        })
        .flatten()
        .map(|surface| surface.name)
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces.dedup();
    surfaces
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_lookup_is_exact_domain_only() {
        for (surface, width, bits) in [
            ("за-умовою", 3usize, 0b011u8),
            ("тотожне?", 3, 0b111),
            ("функція", 4, 0b0010),
            ("визначити", 4, 0b0011),
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
    fn historical_only_surface_cannot_mint_domain_identity() {
        assert_eq!(domain_identity_for_surface("+"), None);
        assert_eq!(domain_identity_for_surface("sqrt"), None);
    }

    #[test]
    fn reverse_projection_uses_domain_identity_not_byte_position() {
        let cadr = domain_identity_for_surface("cadr").unwrap();
        assert!(surfaces_for_identity(cadr).contains(&"cadr"));
        assert_eq!((cadr.width(), cadr.packed_bits()), (4, 0b1011));
    }
}
