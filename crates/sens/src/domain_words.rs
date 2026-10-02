//! Width-safe domain carriers over the shared small-word mechanism.
//!
//! These newtypes separate domain membership at the Rust type boundary without
//! assigning semantic meaning to individual bit patterns. SENS contracts own
//! orientation and role tables; this module owns representation only.
//!
//! Different domains do not implicitly interchange:
//!
//! ```compile_fail
//! use sens::{Bija3, Bit2, Racana2};
//!
//! let structure = Racana2::from_word(Bit2::new(0b01).unwrap());
//! let _: Bija3 = structure;
//! ```
//!
//! Predicate answers are not host booleans:
//!
//! ```compile_fail
//! use sens::PredicateBit;
//!
//! let _: PredicateBit = true;
//! ```

use crate::bits::{Bit1, Bit2, Bit3};

/// Exact one-bit carrier for the SENS predicate-result domain.
///
/// The mapping/orientation of the bit is language-owned and deliberately absent
/// here. In particular, there is no `bool` constructor or conversion.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct PredicateBit(Bit1);

impl core::fmt::Debug for PredicateBit {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(formatter, "PredicateBit({})", self.word().packed_bits())
    }
}

impl PredicateBit {
    /// Wrap an already validated one-bit word.
    pub const fn from_word(word: Bit1) -> Self {
        Self(word)
    }

    /// Recover the mechanical one-bit word without interpreting it.
    pub const fn word(self) -> Bit1 {
        self.0
    }
}

/// Exact two-bit carrier for the ratified racanā2 structural domain.
///
/// This type does not encode which two-bit pattern has which structural role.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Racana2(Bit2);

impl Racana2 {
    /// Wrap an already validated two-bit word.
    pub const fn from_word(word: Bit2) -> Self {
        Self(word)
    }

    /// Recover the mechanical two-bit word without interpreting it.
    pub const fn word(self) -> Bit2 {
        self.0
    }
}

/// Exact three-bit carrier for the ratified bīja3 foundation domain.
///
/// Individual three-bit meanings remain in SENS-owned contracts/witnesses.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Bija3(Bit3);

impl Bija3 {
    /// Wrap an already validated three-bit word.
    pub const fn from_word(word: Bit3) -> Self {
        Self(word)
    }

    /// Recover the mechanical three-bit word without interpreting it.
    pub const fn word(self) -> Bit3 {
        self.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::mem::size_of;

    #[test]
    fn domain_carriers_round_trip_all_mechanical_words() {
        for raw in 0..=1 {
            let word = Bit1::new(raw).unwrap();
            assert!(PredicateBit::from_word(word).word() == word);
        }

        for raw in 0..=3 {
            let word = Bit2::new(raw).unwrap();
            assert!(Racana2::from_word(word).word() == word);
        }

        for raw in 0..=7 {
            let word = Bit3::new(raw).unwrap();
            assert!(Bija3::from_word(word).word() == word);
        }
    }

    #[test]
    fn domain_carriers_remain_one_host_byte() {
        assert_eq!(size_of::<PredicateBit>(), 1);
        assert_eq!(size_of::<Racana2>(), 1);
        assert_eq!(size_of::<Bija3>(), 1);
    }
}
