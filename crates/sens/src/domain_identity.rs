//! Domain-qualified Core identity key for the Sens8/Sid8 exit.
//!
//! This layer carries identity context only. It does not decide whether a
//! coordinate is occupied, callable, primitive, derived, or generated. Those
//! facts remain owned by SENS domain laws and their executable witnesses.
//!
//! Equal packed payloads in different domains remain different identities:
//! D3 `001` is not D4 `0001`.

use crate::{Bija3, BinarySourceWord, CoreD4, CoreD5, CoreD6, CoreD7, CoreD8};
use std::fmt;

/// Exact domain-qualified identity for the current Core operation domains.
///
/// D1 predicate answers and D2 structure are intentionally absent because this
/// key is for D3+ Core semantic identities. D7 and D8 are present as exact
/// domain-qualified identities; their membership does not imply callability.
/// In particular, D7 keeps its Sound7 law and D8 never aliases legacy Sens8.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CoreDomainIdentity {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    D7(CoreD7),
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
            Self::D7(_) => 7,
            Self::D8(_) => 8,
        }
    }

    /// Mechanical payload inside the exact domain.
    ///
    /// The returned byte is never a standalone identity. Callers must retain
    /// the `CoreDomainIdentity` variant/domain alongside it.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
            Self::D7(value) => value.word().packed_bits(),
            Self::D8(value) => value.word().packed_bits(),
        }
    }


    /// Lift only exact Core operation-domain source words into canonical identity.
    ///
    /// D1 predicates and D2 structure use their dedicated carriers. Exact
    /// W3..W8 source words lift to their already-ratified Core domains; this
    /// mechanical bridge still grants neither occupancy nor callability.
    pub const fn from_source_word(source: BinarySourceWord) -> Option<Self> {
        match source {
            BinarySourceWord::W3(word) => Some(Self::D3(Bija3::from_word(word))),
            BinarySourceWord::W4(word) => Some(Self::D4(CoreD4::from_word(word))),
            BinarySourceWord::W5(word) => Some(Self::D5(CoreD5::from_word(word))),
            BinarySourceWord::W6(word) => Some(Self::D6(CoreD6::from_word(word))),
            BinarySourceWord::W7(word) => Some(Self::D7(CoreD7::from_word(word))),
            BinarySourceWord::W8(word) => Some(Self::D8(CoreD8::from_word(word))),
            BinarySourceWord::W1(_) | BinarySourceWord::W2(_) => None,
        }
    }

    /// Lossless exact-width source projection for canonical Core identity.
    pub const fn source_word(self) -> BinarySourceWord {
        match self {
            Self::D3(value) => BinarySourceWord::W3(value.word()),
            Self::D4(value) => BinarySourceWord::W4(value.word()),
            Self::D5(value) => BinarySourceWord::W5(value.word()),
            Self::D6(value) => BinarySourceWord::W6(value.word()),
            Self::D7(value) => BinarySourceWord::W7(value.word()),
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

impl From<CoreD7> for CoreDomainIdentity {
    fn from(value: CoreD7) -> Self {
        Self::D7(value)
    }
}

impl From<CoreD8> for CoreDomainIdentity {
    fn from(value: CoreD8) -> Self {
        Self::D8(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit3, Bit4, Bit5, Bit6, Bit7, Bit8};

    #[test]
    fn source_word_bridge_preserves_exact_domain() {
        for raw in 0..=7 {
            let source = BinarySourceWord::W3(Bit3::new(raw).unwrap());
            let id = CoreDomainIdentity::from_source_word(source).unwrap();
            assert_eq!(id.source_word(), source);
        }
        for raw in 0..=15 {
            let source = BinarySourceWord::W4(Bit4::new(raw).unwrap());
            let id = CoreDomainIdentity::from_source_word(source).unwrap();
            assert_eq!(id.source_word(), source);
        }
        for raw in 0..=31 {
            let source = BinarySourceWord::W5(Bit5::new(raw).unwrap());
            let id = CoreDomainIdentity::from_source_word(source).unwrap();
            assert_eq!(id.source_word(), source);
        }
        for raw in 0..=63 {
            let source = BinarySourceWord::W6(Bit6::new(raw).unwrap());
            let id = CoreDomainIdentity::from_source_word(source).unwrap();
            assert_eq!(id.source_word(), source);
        }

        for raw in 0..=127 {
            let source = BinarySourceWord::W7(Bit7::new(raw).unwrap());
            let id = CoreDomainIdentity::from_source_word(source).unwrap();
            assert_eq!(id.source_word(), source);
        }
        for raw in 0..=255 {
            let source = BinarySourceWord::W8(Bit8::new(raw).unwrap());
            let id = CoreDomainIdentity::from_source_word(source).unwrap();
            assert_eq!(id.source_word(), source);
        }
    }

    #[test]
    fn source_word_bridge_rejects_d1_d2_dedicated_carriers() {
        use crate::{Bit1, Bit2};

        for source in [
            BinarySourceWord::W1(Bit1::new(0).unwrap()),
            BinarySourceWord::W2(Bit2::new(0).unwrap()),
        ] {
            assert!(CoreDomainIdentity::from_source_word(source).is_none());
        }
    }

    #[test]
    fn equal_packed_payloads_in_different_domains_are_distinct_identities() {
        let d3 = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b001).unwrap()));
        let d4 = CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(0b0001).unwrap()));
        let d5 = CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(0b00001).unwrap()));
        let d6 = CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(0b000001).unwrap()));
        let d7 = CoreDomainIdentity::from(CoreD7::from_word(Bit7::new(0b0000001).unwrap()));
        let d8 = CoreDomainIdentity::from(CoreD8::from_word(Bit8::new(0b00000001).unwrap()));

        assert_eq!(d3.packed_bits(), 1);
        assert_eq!(d4.packed_bits(), 1);
        assert_eq!(d5.packed_bits(), 1);
        assert_eq!(d6.packed_bits(), 1);
        assert_eq!(d7.packed_bits(), 1);
        assert_eq!(d8.packed_bits(), 1);

        assert!(d3 != d4);
        assert!(d3 != d5);
        assert!(d3 != d6);
        assert!(d4 != d5);
        assert!(d4 != d6);
        assert!(d5 != d6);
        assert!(d3 != d7);
        assert!(d3 != d8);
        assert!(d6 != d7);
        assert!(d6 != d8);
        assert!(d7 != d8);
    }

    #[test]
    fn exact_domain_width_is_recoverable_without_numeric_inference() {
        let cases = [
            CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b101).unwrap())),
            CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(0b1010).unwrap())),
            CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(0b10101).unwrap())),
            CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(0b101010).unwrap())),
            CoreDomainIdentity::from(CoreD7::from_word(Bit7::new(0b1010101).unwrap())),
            CoreDomainIdentity::from(CoreD8::from_word(Bit8::new(0b10101010).unwrap())),
        ];

        assert_eq!(
            cases.map(CoreDomainIdentity::width),
            [3, 4, 5, 6, 7, 8]
        );
    }

    #[test]
    fn every_domain_preserves_its_full_bounded_payload_range() {
        for raw in 0..=7 {
            let id = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(raw).unwrap()));
            assert_eq!(id.width(), 3);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=15 {
            let id = CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(raw).unwrap()));
            assert_eq!(id.width(), 4);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=31 {
            let id = CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(raw).unwrap()));
            assert_eq!(id.width(), 5);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=63 {
            let id = CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(raw).unwrap()));
            assert_eq!(id.width(), 6);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=127 {
            let id = CoreDomainIdentity::from(CoreD7::from_word(Bit7::new(raw).unwrap()));
            assert_eq!(id.width(), 7);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=255 {
            let id = CoreDomainIdentity::from(CoreD8::from_word(Bit8::new(raw).unwrap()));
            assert_eq!(id.width(), 8);
            assert_eq!(id.packed_bits(), raw);
        }
    }
}
