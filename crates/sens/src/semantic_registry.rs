//! Canonical exact-domain surface registry.
//!
//! Authority: `knowledge/domain-surface-registry.lisp`.
//! Identity is exact domain + exact bits. Historical flat-byte machinery is
//! physically isolated in `legacy_registry.rs`; this module cannot infer a
//! domain from that compatibility axis.

use std::{collections::HashMap, sync::OnceLock};

use crate::{
    Bija3, Bit3, Bit4, Bit5, CoreD4, CoreD5, CoreDomainIdentity,
};

mod generated {
    include!("domain_surface_registry_generated.rs");
}

use generated::DOMAIN_SURFACE_ROWS;

pub(crate) fn exact_domain_identity(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    match width {
        0b11 => Bit3::new(bits)
            .map(Bija3::from_word)
            .map(CoreDomainIdentity::D3),
        0b100 => Bit4::new(bits)
            .map(CoreD4::from_word)
            .map(CoreDomainIdentity::D4),
        0b101 => Bit5::new(bits)
            .map(CoreD5::from_word)
            .map(CoreDomainIdentity::D5),
        _ => None,
    }
}

fn surface_index() -> &'static HashMap<&'static str, CoreDomainIdentity> {
    static INDEX: OnceLock<HashMap<&'static str, CoreDomainIdentity>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in DOMAIN_SURFACE_ROWS {
            let identity = exact_domain_identity(row.width, row.bits).unwrap_or_else(|| {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_lookup_is_exact_domain_only() {
        for (surface, width, bits) in [
            ("за-умовою", 0b11usize, 0b011u8),
            ("тотожне?", 0b11, 0b111),
            ("функція", 0b100, 0b0010),
            ("визначити", 0b100, 0b0011),
            ("перше-від-першого", 0b100, 0b1010),
            ("перше-від-решти", 0b100, 0b1011),
            ("решта-від-решти", 0b100, 0b1101),
            ("+", 0b101, 0b01010),
            ("-", 0b101, 0b01011),
            ("*", 0b101, 0b10010),
            ("/", 0b101, 0b10011),
        ] {
            let identity = domain_identity_for_surface(surface)
                .unwrap_or_else(|| panic!("missing exact-domain surface: {surface}"));
            assert_eq!((identity.width(), identity.packed_bits()), (width, bits));
        }
    }

    #[test]
    fn historical_only_surface_cannot_mint_domain_identity() {
        assert_eq!(domain_identity_for_surface("корінь"), None);
    }

}
