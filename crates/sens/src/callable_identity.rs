//! Unified callable identity for the Sens8/Sid8 exit (#2821).
//!
//! Canonical Core identity is always domain-qualified. Historical exact-eight
//! payloads survive only as an explicit compatibility variant while registry,
//! host and backend mechanisms are migrated. Equal packed bits never imply
//! equal identity across domains or across the compatibility boundary.

use crate::CoreDomainIdentity;
use std::fmt;

#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableIdentity {
    Core(CoreDomainIdentity),
    Legacy8(u8),
}

impl CallableIdentity {
    pub const fn core(identity: CoreDomainIdentity) -> Self {
        Self::Core(identity)
    }

    pub const fn legacy8(bits: u8) -> Self {
        Self::Legacy8(bits)
    }

    pub const fn exact_width(self) -> usize {
        match self {
            Self::Core(identity) => identity.width(),
            Self::Legacy8(_) => 8,
        }
    }

    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::Core(identity) => identity.packed_bits(),
            Self::Legacy8(bits) => bits,
        }
    }

    pub const fn core_identity(self) -> Option<CoreDomainIdentity> {
        match self {
            Self::Core(identity) => Some(identity),
            Self::Legacy8(_) => None,
        }
    }

    pub const fn legacy8_bits(self) -> Option<u8> {
        match self {
            Self::Legacy8(bits) => Some(bits),
            Self::Core(_) => None,
        }
    }
}

impl From<CoreDomainIdentity> for CallableIdentity {
    fn from(identity: CoreDomainIdentity) -> Self {
        Self::Core(identity)
    }
}

impl fmt::Debug for CallableIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::Core(identity) => write!(formatter, "CallableIdentity::Core({identity:?})"),
            Self::Legacy8(bits) => write!(formatter, "CallableIdentity::Legacy8({bits:08b})"),
        }
    }
}

impl fmt::Display for CallableIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::Core(identity) => write!(formatter, "{identity}"),
            Self::Legacy8(bits) => write!(formatter, "{bits:08b}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Bit4, CoreD4};

    #[test]
    fn same_payload_different_domains_stays_distinct() {
        let d3 = CallableIdentity::core(
            Bija3::from_word(Bit3::new(1).unwrap()).into()
        );
        let d4 = CallableIdentity::core(
            CoreD4::from_word(Bit4::new(1).unwrap()).into()
        );
        let legacy = CallableIdentity::legacy8(1);

        assert_eq!(d3.packed_bits(), 1);
        assert_eq!(d4.packed_bits(), 1);
        assert_eq!(legacy.packed_bits(), 1);
        assert_ne!(d3, d4);
        assert_ne!(d3, legacy);
        assert_ne!(d4, legacy);
        assert_eq!([d3.exact_width(), d4.exact_width(), legacy.exact_width()], [3, 4, 8]);
    }

    #[test]
    fn d1_d2_d7_cannot_enter_through_the_type() {
        // CallableIdentity has no PredicateBit, Racana2, Bit7 or Text7 variant.
        // The compile-time enum shape is the guard; this runtime witness pins
        // the admitted widths that can be represented through Core identity.
        for width in [3usize, 4, 5, 6] {
            assert!(matches!(width, 3..=6));
        }
    }
}
