//! Width-preserving semantic identity carried by AST/runtime values.
//!
//! Canonical language identity lives in exact-width `DomainWord` values.
//! Historical 8-bit SENS identifiers survive only as an explicit compatibility
//! projection while the remaining registry/evaluator machinery is migrated.
//! Keeping the two variants distinct prevents accidental zero-padding from
//! becoming semantic equality.

use crate::{DomainWord, Sens8};
use std::fmt;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum SemanticRef {
    Domain(DomainWord),
    Legacy8(Sens8),
}

impl SemanticRef {
    pub const fn domain(word: DomainWord) -> Self {
        Self::Domain(word)
    }

    pub const fn legacy8(word: Sens8) -> Self {
        Self::Legacy8(word)
    }

    pub const fn exact_width(self) -> usize {
        match self {
            Self::Domain(word) => word.width(),
            Self::Legacy8(_) => 8,
        }
    }

    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::Domain(word) => word.packed_bits(),
            Self::Legacy8(word) => word.packed_byte(),
        }
    }

    pub const fn domain_word(self) -> Option<DomainWord> {
        match self {
            Self::Domain(word) => Some(word),
            Self::Legacy8(_) => None,
        }
    }

    /// Compatibility projection only. Canonical domain identities deliberately
    /// do not acquire an 8-bit meaning merely because their payload fits in u8.
    pub const fn legacy8_word(self) -> Option<Sens8> {
        match self {
            Self::Legacy8(word) => Some(word),
            Self::Domain(_) => None,
        }
    }

    pub const fn from_width_bits(width: usize, bits: u8) -> Option<Self> {
        if width == 8 {
            return Some(Self::Legacy8(Sens8::from_packed_byte(bits)));
        }
        match DomainWord::from_width_bits(width, bits) {
            Some(word) => Some(Self::Domain(word)),
            None => None,
        }
    }
}

impl From<DomainWord> for SemanticRef {
    fn from(value: DomainWord) -> Self {
        Self::Domain(value)
    }
}

impl From<Sens8> for SemanticRef {
    fn from(value: Sens8) -> Self {
        Self::Legacy8(value)
    }
}

impl fmt::Display for SemanticRef {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::Domain(word) => write!(f, "{:0width$b}", word.packed_bits(), width = word.width()),
            Self::Legacy8(word) => write!(f, "{word}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3};

    #[test]
    fn legacy_and_domain_bits_do_not_alias() {
        let d3 = SemanticRef::domain(DomainWord::D3(Bija3::from_word(
            Bit3::new(0b101).unwrap(),
        )));
        let legacy = SemanticRef::legacy8(Sens8::from_packed_byte(0b0000_0101));

        assert_ne!(d3, legacy);
        assert_eq!(d3.packed_bits(), legacy.packed_bits());
        assert_eq!(d3.exact_width(), 3);
        assert_eq!(legacy.exact_width(), 8);
        assert_eq!(d3.to_string(), "101");
        assert_eq!(legacy.to_string(), "00000101");
    }

    #[test]
    fn decoding_preserves_width_as_identity() {
        let d3 = SemanticRef::from_width_bits(3, 1).unwrap();
        let d4 = SemanticRef::from_width_bits(4, 1).unwrap();
        let legacy = SemanticRef::from_width_bits(8, 1).unwrap();

        assert_ne!(d3, d4);
        assert_ne!(d4, legacy);
        assert_eq!(d3.exact_width(), 3);
        assert_eq!(d4.exact_width(), 4);
        assert_eq!(legacy.exact_width(), 8);
        assert!(SemanticRef::from_width_bits(7, 1).is_none());
    }
}
