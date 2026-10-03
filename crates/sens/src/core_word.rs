//! Domain-qualified carrier for callable Core coordinates.
//!
//! This is a representation boundary only. A CoreWord carries exact bits plus
//! the Core domain that owns those bits; it does not encode operation names or
//! prove that a coordinate is executable. Admission remains contract/law-owned.
//!
//! Equal packed payloads in different domains remain different identities:
//!
//! ```
//! use sens::{Bija3, Bit3, Bit4, CoreD4, CoreWord};
//!
//! let d3 = CoreWord::D3(Bija3::from_word(Bit3::new(0b011).unwrap()));
//! let d4 = CoreWord::D4(CoreD4::from_word(Bit4::new(0b0011).unwrap()));
//! assert_ne!(d3, d4);
//! ```
//!
//! Legacy Sens8 has no implicit conversion into this carrier:
//!
//! ```compile_fail
//! use sens::{CoreWord, Sens8};
//!
//! let legacy = Sens8::from_packed_byte(0b0000_0011);
//! let _: CoreWord = legacy;
//! ```

use crate::{Bija3, BinarySourceWord, CoreD4, CoreD5, CoreD6};

/// Exact domain + exact binary coordinate for callable Core strata.
///
/// D1 predicates, D2 structure, and D7 Sound/Ordinal are deliberately absent:
/// width alone never grants callable identity.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CoreWord {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
}

impl CoreWord {
    /// Exact domain width. This is a representation fact, not operation meaning.
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
        }
    }

    /// Mechanical payload. It must never be detached from the domain variant
    /// when used as canonical identity.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(word) => word.word().packed_bits(),
            Self::D4(word) => word.word().packed_bits(),
            Self::D5(word) => word.word().packed_bits(),
            Self::D6(word) => word.word().packed_bits(),
        }
    }

    /// Admit only exact source widths belonging to callable Core strata.
    ///
    /// This performs no owner-map/executability lookup.
    pub const fn from_source_word(source: BinarySourceWord) -> Option<Self> {
        match source {
            BinarySourceWord::W3(word) => Some(Self::D3(Bija3::from_word(word))),
            BinarySourceWord::W4(word) => Some(Self::D4(CoreD4::from_word(word))),
            BinarySourceWord::W5(word) => Some(Self::D5(CoreD5::from_word(word))),
            BinarySourceWord::W6(word) => Some(Self::D6(CoreD6::from_word(word))),
            BinarySourceWord::W1(_)
            | BinarySourceWord::W2(_)
            | BinarySourceWord::W7(_)
            | BinarySourceWord::W8(_) => None,
        }
    }

    /// Exact source projection; width and domain remain recoverable.
    pub const fn source_word(self) -> BinarySourceWord {
        match self {
            Self::D3(word) => BinarySourceWord::W3(word.word()),
            Self::D4(word) => BinarySourceWord::W4(word.word()),
            Self::D5(word) => BinarySourceWord::W5(word.word()),
            Self::D6(word) => BinarySourceWord::W6(word.word()),
        }
    }
}

impl core::fmt::Debug for CoreWord {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(
            formatter,
            "CoreWord<D{}>({:0width$b})",
            self.width(),
            self.packed_bits(),
            width = self.width()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8};

    #[test]
    fn d3_through_d6_round_trip_without_width_loss() {
        for raw in 0..=7 {
            let source = BinarySourceWord::W3(Bit3::new(raw).unwrap());
            let word = CoreWord::from_source_word(source).unwrap();
            assert_eq!(word.width(), 3);
            assert_eq!(word.source_word(), source);
        }
        for raw in 0..=15 {
            let source = BinarySourceWord::W4(Bit4::new(raw).unwrap());
            let word = CoreWord::from_source_word(source).unwrap();
            assert_eq!(word.width(), 4);
            assert_eq!(word.source_word(), source);
        }
        for raw in 0..=31 {
            let source = BinarySourceWord::W5(Bit5::new(raw).unwrap());
            let word = CoreWord::from_source_word(source).unwrap();
            assert_eq!(word.width(), 5);
            assert_eq!(word.source_word(), source);
        }
        for raw in 0..=63 {
            let source = BinarySourceWord::W6(Bit6::new(raw).unwrap());
            let word = CoreWord::from_source_word(source).unwrap();
            assert_eq!(word.width(), 6);
            assert_eq!(word.source_word(), source);
        }
    }

    #[test]
    fn same_payload_in_different_domains_never_collapses() {
        let d3 = CoreWord::from_source_word(BinarySourceWord::W3(Bit3::new(1).unwrap())).unwrap();
        let d4 = CoreWord::from_source_word(BinarySourceWord::W4(Bit4::new(1).unwrap())).unwrap();
        let d5 = CoreWord::from_source_word(BinarySourceWord::W5(Bit5::new(1).unwrap())).unwrap();
        let d6 = CoreWord::from_source_word(BinarySourceWord::W6(Bit6::new(1).unwrap())).unwrap();

        assert!(d3 != d4);
        assert!(d4 != d5);
        assert!(d5 != d6);
        assert_eq!(d3.packed_bits(), 1);
        assert_eq!(d4.packed_bits(), 1);
        assert_eq!(d5.packed_bits(), 1);
        assert_eq!(d6.packed_bits(), 1);
    }

    #[test]
    fn non_callable_widths_are_rejected_by_representation_boundary() {
        for source in [
            BinarySourceWord::W1(Bit1::new(0).unwrap()),
            BinarySourceWord::W2(Bit2::new(0).unwrap()),
            BinarySourceWord::W7(Bit7::new(0).unwrap()),
            BinarySourceWord::W8(Bit8::new(0).unwrap()),
        ] {
            assert!(CoreWord::from_source_word(source).is_none());
        }
    }
}
