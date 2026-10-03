//! Domain-qualified callable identity for the staged Sens8 exit (#2821).
//!
//! This module carries only canonical callable-domain identity. Historical
//! exact-eight runtime identity stays in explicitly named LegacySid/LegacyCall
//! AST/value variants while downstream layers migrate.

use crate::{Bija3, CoreD4, CoreD5, CoreD6};
use std::fmt;

/// Canonical callable identities admitted by the current domain ontology.
///
/// D1 predicate answers, D2 structural words, and D7 sound/ordinal carriers are
/// intentionally absent: having bits does not make a domain callable.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableDomainId {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
}

impl CallableDomainId {
    pub const fn width(self) -> u8 {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
        }
    }

    /// Mechanical bits inside the already-known domain.
    /// Detached from the domain, this byte has no semantic identity.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
        }
    }

    pub(crate) const fn transport_domain_tag(self) -> u8 {
        self.width()
    }

    pub(crate) fn from_transport_parts(domain: u8, payload: u8) -> Option<Self> {
        match domain {
            3 => Some(Self::D3(Bija3::from_word(crate::Bit3::new(payload)?))),
            4 => Some(Self::D4(CoreD4::from_word(crate::Bit4::new(payload)?))),
            5 => Some(Self::D5(CoreD5::from_word(crate::Bit5::new(payload)?))),
            6 => Some(Self::D6(CoreD6::from_word(crate::Bit6::new(payload)?))),
            _ => None,
        }
    }
}

impl fmt::Display for CallableDomainId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "D{}:{:0width$b}",
            self.width(),
            self.packed_bits(),
            width = self.width() as usize
        )
    }
}

impl fmt::Debug for CallableDomainId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "CallableDomainId({self})")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn equal_packed_payloads_in_different_domains_are_not_equal() {
        let d3 = CallableDomainId::D3(Bija3::from_word(crate::Bit3::new(0b101).unwrap()));
        let d4 = CallableDomainId::D4(CoreD4::from_word(crate::Bit4::new(0b0101).unwrap()));
        let d5 = CallableDomainId::D5(CoreD5::from_word(crate::Bit5::new(0b00101).unwrap()));
        let d6 = CallableDomainId::D6(CoreD6::from_word(crate::Bit6::new(0b000101).unwrap()));

        assert_ne!(d3, d4);
        assert_ne!(d4, d5);
        assert_ne!(d5, d6);
        assert_eq!(d3.packed_bits(), 5);
        assert_eq!(d4.packed_bits(), 5);
        assert_eq!(d5.packed_bits(), 5);
        assert_eq!(d6.packed_bits(), 5);
    }

    #[test]
    fn transport_domain_tag_is_explicit_and_round_trips() {
        for (domain, max) in [(3u8, 7u8), (4, 15), (5, 31), (6, 63)] {
            for payload in 0..=max {
                let value = CallableDomainId::from_transport_parts(domain, payload)
                    .expect("valid domain word");
                assert_eq!(value.width(), domain);
                assert_eq!(value.transport_domain_tag(), domain);
                assert_eq!(value.packed_bits(), payload);
            }
        }

        assert!(CallableDomainId::from_transport_parts(2, 0).is_none());
        assert!(CallableDomainId::from_transport_parts(7, 0).is_none());
        assert!(CallableDomainId::from_transport_parts(3, 8).is_none());
        assert!(CallableDomainId::from_transport_parts(4, 16).is_none());
        assert!(CallableDomainId::from_transport_parts(5, 32).is_none());
        assert!(CallableDomainId::from_transport_parts(6, 64).is_none());
    }
}
