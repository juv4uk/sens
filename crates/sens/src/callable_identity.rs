//! Domain-qualified callable identity for the staged Sens8 exit (#2821).
//!
//! Canonical callable identity is a binary object inside its semantic domain.
//! The exact-eight legacy runtime remains available only through an explicit
//! compatibility wrapper while downstream evaluator/registry layers migrate.
//!
//! No implicit widening, truncation, low-bit mapping, human-name lookup, or
//! width=>domain inference lives here.

use crate::{Bija3, CoreD4, CoreD5, CoreD6, Sens8};
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

/// Explicit compatibility wrapper for the historical universal eight-bit path.
///
/// Construction is intentionally named: callers cannot obtain this wrapper via
/// an implicit conversion, so every remaining legacy producer is visible.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct LegacySens8(Sens8);

impl LegacySens8 {
    pub const fn new(value: Sens8) -> Self {
        Self(value)
    }

    pub const fn sens8(self) -> Sens8 {
        self.0
    }
}

impl fmt::Display for LegacySens8 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

impl fmt::Debug for LegacySens8 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "LegacySens8({})", self.0)
    }
}

/// Staged runtime/AST callable carrier.
///
/// Domain is canonical. LegacySens8 exists only so the old parser/lowering
/// path can keep compiling while it is migrated family by family.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableIdentity {
    Domain(CallableDomainId),
    LegacySens8(LegacySens8),
}

impl CallableIdentity {
    pub const fn domain(value: CallableDomainId) -> Self {
        Self::Domain(value)
    }

    /// Explicit compatibility constructor. Do not replace this with From.
    pub const fn legacy_sens8(value: Sens8) -> Self {
        Self::LegacySens8(LegacySens8::new(value))
    }

    pub const fn canonical_domain(self) -> Option<CallableDomainId> {
        match self {
            Self::Domain(value) => Some(value),
            Self::LegacySens8(_) => None,
        }
    }

    pub const fn legacy_projection(self) -> Option<Sens8> {
        match self {
            Self::Domain(_) => None,
            Self::LegacySens8(value) => Some(value.sens8()),
        }
    }
}

impl fmt::Display for CallableIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Domain(value) => value.fmt(formatter),
            Self::LegacySens8(value) => value.fmt(formatter),
        }
    }
}

impl fmt::Debug for CallableIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Domain(value) => value.fmt(formatter),
            Self::LegacySens8(value) => value.fmt(formatter),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn equal_packed_payloads_in_different_domains_are_not_equal() {
        let d3 = CallableIdentity::domain(CallableDomainId::D3(Bija3::from_word(
            crate::Bit3::new(0b101).unwrap(),
        )));
        let d4 = CallableIdentity::domain(CallableDomainId::D4(CoreD4::from_word(
            crate::Bit4::new(0b0101).unwrap(),
        )));
        let d5 = CallableIdentity::domain(CallableDomainId::D5(CoreD5::from_word(
            crate::Bit5::new(0b00101).unwrap(),
        )));
        let d6 = CallableIdentity::domain(CallableDomainId::D6(CoreD6::from_word(
            crate::Bit6::new(0b000101).unwrap(),
        )));

        assert_ne!(d3, d4);
        assert_ne!(d4, d5);
        assert_ne!(d5, d6);
        assert_eq!(d3.canonical_domain().unwrap().packed_bits(), 5);
        assert_eq!(d4.canonical_domain().unwrap().packed_bits(), 5);
        assert_eq!(d5.canonical_domain().unwrap().packed_bits(), 5);
        assert_eq!(d6.canonical_domain().unwrap().packed_bits(), 5);
    }

    #[test]
    fn legacy_eight_bit_identity_never_equals_domain_identity() {
        let domain = CallableIdentity::domain(CallableDomainId::D3(Bija3::from_word(
            crate::Bit3::new(0b101).unwrap(),
        )));
        let legacy = CallableIdentity::legacy_sens8(crate::sens!(00000101));

        assert_ne!(domain, legacy);
        assert_eq!(legacy.legacy_projection(), Some(crate::sens!(00000101)));
        assert_eq!(domain.legacy_projection(), None);
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
