//! Narrow compatibility adapter around the historical flat registry.
//!
//! Canonical exact-domain modules must not import `legacy_registry` directly.
//! This module owns the only admitted old-surface/old-byte compatibility API.
//! Every byte->domain row below is an explicit proved migration fact; no
//! truncation, extension, or numeric inference is permitted.

use crate::{
    legacy_registry, Bija3, Bit3, Bit4, Bit5, CoreD4, CoreD5, CoreDomainIdentity, Sens8,
};

pub(crate) type LegacyRegistryId = Sens8;

pub(crate) fn id_for_surface(name: &str) -> Option<LegacyRegistryId> {
    legacy_registry::id_for_surface(name)
}

pub(crate) fn stable_surfaces_for_id(id: LegacyRegistryId) -> Vec<&'static str> {
    legacy_registry::stable_surfaces_for_id(id)
}

pub(crate) fn admitted_surfaces_for_id(id: LegacyRegistryId) -> Vec<&'static str> {
    legacy_registry::admitted_surfaces_for_id(id)
}

pub(crate) fn admitted_surfaces_with_namespace_for_id(
    id: LegacyRegistryId,
) -> Vec<(&'static str, &'static str)> {
    legacy_registry::admitted_surfaces_with_namespace_for_id(id)
}

pub(crate) fn admitted_ids() -> Vec<LegacyRegistryId> {
    legacy_registry::admitted_ids()
}

pub(crate) fn id_bits(id: LegacyRegistryId) -> String {
    legacy_registry::id_bits(id)
}

/// Historical executable byte -> already-ratified exact-domain successor.
///
/// This adapter is one-way compatibility only. It cannot create occupancy,
/// surfaces, role, or callability.
pub(crate) fn domain_successor_from_byte(byte: u8) -> Option<CoreDomainIdentity> {
    let d3 = |raw| CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()));
    let d4 = |raw| CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()));
    let d5 = |raw| CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(raw).unwrap()));

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
        0b0000_1100 => Some(d5(0b01010)),
        0b0000_1101 => Some(d5(0b01011)),
        0b0001_1010 => Some(d5(0b01110)),
        0b0001_1011 => Some(d5(0b01111)),
        0b0000_1110 => Some(d5(0b10010)),
        0b0000_1111 => Some(d5(0b10011)),
        _ => None,
    }
}

/// Temporary same-closure alias required by legacy recursive Core bodies.
///
/// Exact identity is owned by D5. The historical byte only selects a
/// compatibility mechanism slot while old Core source still contains that byte.
pub(crate) fn d5_bootstrap_identity_from_byte(byte: u8) -> Option<CoreDomainIdentity> {
    let d5 = |raw| CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(raw).unwrap()));
    match byte {
        0b0010_1001 => Some(d5(0b10000)),
        0b0010_1010 => Some(d5(0b10001)),
        0b0001_0100 => Some(d5(0b10011)),
        0b0010_1101 => Some(d5(0b11100)),
        0b0010_1100 => Some(d5(0b11101)),
        0b1010_1100 => Some(d5(0b11111)),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compatibility_mapping_is_explicit_not_numeric_projection() {
        assert_eq!(
            domain_successor_from_byte(0b0011_0100)
                .map(|identity| (identity.width(), identity.packed_bits())),
            Some((4, 0b1011))
        );
        assert_eq!(
            d5_bootstrap_identity_from_byte(0b0010_1010)
                .map(|identity| (identity.width(), identity.packed_bits())),
            Some((5, 0b10001))
        );
        assert_eq!(domain_successor_from_byte(0b1111_1111), None);
        assert_eq!(d5_bootstrap_identity_from_byte(0b1111_1111), None);
    }

    #[test]
    fn flat_surface_lookup_remains_compatibility_only() {
        assert_eq!(id_for_surface("+"), Some(crate::sens!(00001100)));
    }
}
