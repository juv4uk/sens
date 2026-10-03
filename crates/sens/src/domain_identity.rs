//! Exact domain-qualified identity for the ratified D1-D8 SENS ladder.
//!
//! This layer carries identity context only. It does not decide whether a
//! coordinate is occupied, callable, primitive, derived, generated, sound,
//! ordinal, or otherwise semantically admitted. Those facts remain owned by
//! SENS domain laws and their executable witnesses.
//!
//! Equal packed payloads in different domains remain different identities:
//! D3 `001` is not D4 `0001`, and D8 is not legacy Sens8/Function8.

use crate::{
    Bija3, BinarySourceWord, CoreD4, CoreD5, CoreD6, CoreD7, CoreD8, PredicateBit, Racana2,
};
use std::fmt;

/// Exact identity across the complete owner-ratified D1-D8 domain ladder.
///
/// This is the general semantic coordinate carrier. It deliberately does not
/// imply callability: D1 predicates, D2 structure and D7 Sound7/local ordinals
/// remain their own domain laws.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum DomainIdentity {
    D1(PredicateBit),
    D2(Racana2),
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    D7(CoreD7),
    D8(CoreD8),
}

impl DomainIdentity {
    /// Exact domain width carried by this identity.
    pub const fn width(self) -> usize {
        match self {
            Self::D1(_) => 1,
            Self::D2(_) => 2,
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::D7(_) => 7,
            Self::D8(_) => 8,
        }
    }

    /// Mechanical payload inside the exact domain.
    ///
    /// The returned byte is never a standalone semantic identity. The domain
    /// variant must remain attached to the payload.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D1(value) => value.word().packed_bits(),
            Self::D2(value) => value.word().packed_bits(),
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
            Self::D7(value) => value.word().packed_bits(),
            Self::D8(value) => value.word().packed_bits(),
        }
    }

    /// Lift an exact-width source word into the correspondingly ratified domain.
    ///
    /// This mapping is mechanical width/domain admission only. It does not say
    /// that a coordinate is occupied or callable.
    pub const fn from_source_word(source: BinarySourceWord) -> Self {
        match source {
            BinarySourceWord::W1(word) => Self::D1(PredicateBit::from_word(word)),
            BinarySourceWord::W2(word) => Self::D2(Racana2::from_word(word)),
            BinarySourceWord::W3(word) => Self::D3(Bija3::from_word(word)),
            BinarySourceWord::W4(word) => Self::D4(CoreD4::from_word(word)),
            BinarySourceWord::W5(word) => Self::D5(CoreD5::from_word(word)),
            BinarySourceWord::W6(word) => Self::D6(CoreD6::from_word(word)),
            BinarySourceWord::W7(word) => Self::D7(CoreD7::from_word(word)),
            BinarySourceWord::W8(word) => Self::D8(CoreD8::from_word(word)),
        }
    }

    /// Lossless exact-width source projection.
    pub const fn source_word(self) -> BinarySourceWord {
        match self {
            Self::D1(value) => BinarySourceWord::W1(value.word()),
            Self::D2(value) => BinarySourceWord::W2(value.word()),
            Self::D3(value) => BinarySourceWord::W3(value.word()),
            Self::D4(value) => BinarySourceWord::W4(value.word()),
            Self::D5(value) => BinarySourceWord::W5(value.word()),
            Self::D6(value) => BinarySourceWord::W6(value.word()),
            Self::D7(value) => BinarySourceWord::W7(value.word()),
            Self::D8(value) => BinarySourceWord::W8(value.word()),
        }
    }
}

impl fmt::Debug for DomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let width = self.width();
        write!(
            formatter,
            "DomainIdentity<D{width}>({:0width$b})",
            self.packed_bits()
        )
    }
}

impl fmt::Display for DomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{:0width$b}",
            self.packed_bits(),
            width = self.width()
        )
    }
}

/// Exact domain-qualified identity for Core operation domains.
///
/// D1 predicate answers, D2 structure and D7 Sound7/local ordinals are
/// intentionally absent because this key is for operation/callable routing.
/// D8 is included as a canonical exact domain and is never reconstructed from
/// legacy Sens8 merely because both occupy eight physical bits.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CoreDomainIdentity {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    D8(CoreD8),
}

impl fmt::Debug for CoreDomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let width = self.width();
        write!(
            formatter,
            "CoreDomainIdentity<D{width}>({:0width$b})",
            self.packed_bits()
        )
    }
}

impl fmt::Display for CoreDomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{:0width$b}",
            self.packed_bits(),
            width = self.width()
        )
    }
}

impl CoreDomainIdentity {
    /// Exact domain width carried by this identity.
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::D8(_) => 8,
        }
    }

    /// Mechanical payload inside the exact domain.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
            Self::D8(value) => value.word().packed_bits(),
        }
    }

    /// Lift only exact Core operation-domain source words into this carrier.
    ///
    /// D1 predicates, D2 structure and D7 Sound7/local ordinals are rejected.
    /// W8 maps to canonical D8, never to legacy Sens8/Function8.
    pub const fn from_source_word(source: BinarySourceWord) -> Option<Self> {
        match source {
            BinarySourceWord::W3(word) => Some(Self::D3(Bija3::from_word(word))),
            BinarySourceWord::W4(word) => Some(Self::D4(CoreD4::from_word(word))),
            BinarySourceWord::W5(word) => Some(Self::D5(CoreD5::from_word(word))),
            BinarySourceWord::W6(word) => Some(Self::D6(CoreD6::from_word(word))),
            BinarySourceWord::W8(word) => Some(Self::D8(CoreD8::from_word(word))),
            BinarySourceWord::W1(_) | BinarySourceWord::W2(_) | BinarySourceWord::W7(_) => None,
        }
    }

    /// Lossless exact-width source projection for canonical Core identity.
    pub const fn source_word(self) -> BinarySourceWord {
        match self {
            Self::D3(value) => BinarySourceWord::W3(value.word()),
            Self::D4(value) => BinarySourceWord::W4(value.word()),
            Self::D5(value) => BinarySourceWord::W5(value.word()),
            Self::D6(value) => BinarySourceWord::W6(value.word()),
            Self::D8(value) => BinarySourceWord::W8(value.word()),
        }
    }
}

impl From<Bija3> for CoreDomainIdentity {
    fn from(value: Bija3) -> Self {
        Self::D3(value)
    }
}

impl From<CoreD4> for CoreDomainIdentity {
    fn from(value: CoreD4) -> Self {
        Self::D4(value)
    }
}

impl From<CoreD5> for CoreDomainIdentity {
    fn from(value: CoreD5) -> Self {
        Self::D5(value)
    }
}

impl From<CoreD6> for CoreDomainIdentity {
    fn from(value: CoreD6) -> Self {
        Self::D6(value)
    }
}

impl From<CoreD8> for CoreDomainIdentity {
    fn from(value: CoreD8) -> Self {
        Self::D8(value)
    }
}

impl From<CoreDomainIdentity> for DomainIdentity {
    fn from(value: CoreDomainIdentity) -> Self {
        match value {
            CoreDomainIdentity::D3(word) => Self::D3(word),
            CoreDomainIdentity::D4(word) => Self::D4(word),
            CoreDomainIdentity::D5(word) => Self::D5(word),
            CoreDomainIdentity::D6(word) => Self::D6(word),
            CoreDomainIdentity::D8(word) => Self::D8(word),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8};

    #[test]
    fn complete_domain_identity_round_trips_w1_through_w8() {
        let sources = [
            BinarySourceWord::W1(Bit1::new(1).unwrap()),
            BinarySourceWord::W2(Bit2::new(1).unwrap()),
            BinarySourceWord::W3(Bit3::new(1).unwrap()),
            BinarySourceWord::W4(Bit4::new(1).unwrap()),
            BinarySourceWord::W5(Bit5::new(1).unwrap()),
            BinarySourceWord::W6(Bit6::new(1).unwrap()),
            BinarySourceWord::W7(Bit7::new(1).unwrap()),
            BinarySourceWord::W8(Bit8::new(1).unwrap()),
        ];

        let identities = sources.map(DomainIdentity::from_source_word);
        assert_eq!(identities.map(DomainIdentity::width), [1, 2, 3, 4, 5, 6, 7, 8]);
        assert_eq!(identities.map(DomainIdentity::source_word), sources);
    }

    #[test]
    fn equal_payloads_across_d1_d8_remain_distinct_identities() {
        let sources = [
            BinarySourceWord::W1(Bit1::new(1).unwrap()),
            BinarySourceWord::W2(Bit2::new(1).unwrap()),
            BinarySourceWord::W3(Bit3::new(1).unwrap()),
            BinarySourceWord::W4(Bit4::new(1).unwrap()),
            BinarySourceWord::W5(Bit5::new(1).unwrap()),
            BinarySourceWord::W6(Bit6::new(1).unwrap()),
            BinarySourceWord::W7(Bit7::new(1).unwrap()),
            BinarySourceWord::W8(Bit8::new(1).unwrap()),
        ];
        let identities = sources.map(DomainIdentity::from_source_word);

        assert!(identities.iter().all(|identity| identity.packed_bits() == 1));
        for left in 0..identities.len() {
            for right in (left + 1)..identities.len() {
                assert!(identities[left] != identities[right]);
            }
        }
    }

    #[test]
    fn core_operation_identity_accepts_d8_but_not_d7() {
        let d8_source = BinarySourceWord::W8(Bit8::new(0b1010_0101).unwrap());
        let d8 = CoreDomainIdentity::from_source_word(d8_source).expect("D8 is a Core domain");
        assert_eq!(d8.width(), 8);
        assert_eq!(d8.source_word(), d8_source);

        let d7_source = BinarySourceWord::W7(Bit7::new(0b101_0101).unwrap());
        assert!(CoreDomainIdentity::from_source_word(d7_source).is_none());
        assert_eq!(DomainIdentity::from_source_word(d7_source).width(), 7);
    }

    #[test]
    fn core_equal_payloads_remain_distinct_including_d8() {
        let cases = [
            CoreDomainIdentity::from(Bija3::from_word(Bit3::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD8::from_word(Bit8::new(1).unwrap())),
        ];

        assert_eq!(cases.map(CoreDomainIdentity::width), [3, 4, 5, 6, 8]);
        assert!(cases.iter().all(|identity| identity.packed_bits() == 1));
        for left in 0..cases.len() {
            for right in (left + 1)..cases.len() {
                assert!(cases[left] != cases[right]);
            }
        }
    }

    #[test]
    fn every_core_domain_preserves_its_full_bounded_payload_range() {
        for raw in 0..=7 {
            let id = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(raw).unwrap()));
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=15 {
            let id = CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(raw).unwrap()));
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=31 {
            let id = CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(raw).unwrap()));
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=63 {
            let id = CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(raw).unwrap()));
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=255 {
            let id = CoreDomainIdentity::from(CoreD8::from_word(Bit8::new(raw).unwrap()));
            assert_eq!(id.packed_bits(), raw);
        }
    }
}
