//! Width-safe logical domain carriers over exact-width words.
//!
//! These newtypes separate domain membership at the Rust type boundary without
//! assigning semantic meaning to individual bit patterns. SENS contracts own
//! orientation and role tables; this module owns typed logical representation.
//!
//! The carriers are not canonical physical program cells. A program is packed
//! separately at the bit level by `BitPacker`/`PackedBitstream`. Rust's
//! byte-addressed ABI may use a host byte for an individual transient value,
//! but that host fact never becomes SENS semantic width.
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

use crate::bits::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8};
use crate::Bit9;

/// Exact one-bit logical carrier for the SENS predicate-result domain.
///
/// The mapping/orientation of the bit is language-owned and deliberately absent
/// here. In particular, there is no `bool` constructor or conversion.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct PredicateBit(Bit1);

impl PredicateBit {
    /// Wrap an already validated one-bit logical word.
    pub const fn from_word(word: Bit1) -> Self {
        Self(word)
    }

    /// Recover the mechanical one-bit word without interpreting it.
    pub const fn word(self) -> Bit1 {
        self.0
    }
}

/// Exact two-bit logical carrier for the ratified racanā2 structural domain.
///
/// This type does not encode which two-bit pattern has which structural role.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Racana2(Bit2);

impl Racana2 {
    /// Wrap an already validated two-bit logical word.
    pub const fn from_word(word: Bit2) -> Self {
        Self(word)
    }

    /// Recover the mechanical two-bit word without interpreting it.
    pub const fn word(self) -> Bit2 {
        self.0
    }
}

/// Exact three-bit logical carrier for the ratified bīja3 foundation domain.
///
/// Individual three-bit meanings remain in SENS-owned contracts/witnesses.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Bija3(Bit3);

impl Bija3 {
    /// Wrap an already validated three-bit logical word.
    pub const fn from_word(word: Bit3) -> Self {
        Self(word)
    }

    /// Recover the mechanical three-bit word without interpreting it.
    pub const fn word(self) -> Bit3 {
        self.0
    }
}

/// Exact four-bit logical carrier for the ratified Core.D4 bootstrap domain.
///
/// This type proves only exact Core.D4 membership. The occupied/free map and
/// executable laws remain owned by #2169 and SENS conformance evidence.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD4(Bit4);

impl CoreD4 {
    /// Wrap an already validated four-bit logical word as a Core.D4 member.
    pub const fn from_word(word: Bit4) -> Self {
        Self(word)
    }

    /// Recover the mechanical four-bit word without interpreting it.
    pub const fn word(self) -> Bit4 {
        self.0
    }
}

/// Exact five-bit logical carrier.
///
/// D5 semantic ratification is governed by its current contract. This type
/// proves exact width only; resident meaning remains domain-law owned.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD5(Bit5);

impl CoreD5 {
    /// Wrap an already validated five-bit logical word.
    pub const fn from_word(word: Bit5) -> Self {
        Self(word)
    }

    /// Recover the mechanical five-bit word without interpreting it.
    pub const fn word(self) -> Bit5 {
        self.0
    }
}

/// Exact six-bit logical carrier for current Core.D6 semantic identity.
///
/// Contract 11.6 / #3393 ratifies D6 64/64. This type proves exact D6
/// membership; callable mechanism remains a separate fact and may fail-closed.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD6(Bit6);

impl CoreD6 {
    /// Wrap an already validated six-bit logical word.
    pub const fn from_word(word: Bit6) -> Self {
        Self(word)
    }

    /// Recover the mechanical six-bit word without interpreting it.
    pub const fn word(self) -> Bit6 {
        self.0
    }
}

/// Exact seven-bit logical carrier for the ratified D7 Sound7/local-ordinal domain.
///
/// This proves D7 membership only. Sound7/local-ordinal laws own interpretation;
/// callability or selector geometry must never be inferred from its width.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct SoundD7(Bit7);

impl SoundD7 {
    /// Wrap an already validated seven-bit logical word.
    pub const fn from_word(word: Bit7) -> Self {
        Self(word)
    }

    /// Recover the mechanical seven-bit word without interpreting it.
    pub const fn word(self) -> Bit7 {
        self.0
    }
}

/// Exact eight-bit logical carrier for the ratified D8 domain.
///
/// This carrier remains distinct from historical flat Sens8/Sid8 bytes. It
/// proves exact width/domain typing; physical program bytes are produced only
/// by the program-level packing layer.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD8(Bit8);

impl CoreD8 {
    /// Wrap an already validated eight-bit logical word.
    pub const fn from_word(word: Bit8) -> Self {
        Self(word)
    }

    /// Recover the mechanical eight-bit word without interpreting it.
    pub const fn word(self) -> Bit8 {
        self.0
    }
}

/// Exact nine-bit carrier for owner-ratified D9 semantic identity (#4008).
///
/// This proves only exact D9 membership. It deliberately grants no callable
/// mechanism and never routes through SID8/Function8.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD9(Bit9);

impl CoreD9 {
    pub const fn from_word(word: Bit9) -> Self {
        Self(word)
    }

    pub const fn word(self) -> Bit9 {
        self.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn domain_carriers_round_trip_all_logical_words() {
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

        for raw in 0..=15 {
            let word = Bit4::new(raw).unwrap();
            assert!(CoreD4::from_word(word).word() == word);
        }

        for raw in 0..=31 {
            let word = Bit5::new(raw).unwrap();
            assert!(CoreD5::from_word(word).word() == word);
        }

        for raw in 0..=63 {
            let word = Bit6::new(raw).unwrap();
            assert!(CoreD6::from_word(word).word() == word);
        }

        for raw in 0..=127 {
            let word = Bit7::new(raw).unwrap();
            assert!(SoundD7::from_word(word).word() == word);
        }

        for raw in 0..=255 {
            let word = Bit8::new(raw).unwrap();
            assert!(CoreD8::from_word(word).word() == word);
        }

        for raw in 0..=511 {
            let word = Bit9::new(raw).unwrap();
            assert!(CoreD9::from_word(word).word() == word);
        }
    }

    #[test]
    fn host_container_size_is_separate_from_domain_width() {
        use std::mem::size_of;

        assert_eq!(size_of::<PredicateBit>(), 1);
        assert_eq!(size_of::<Racana2>(), 1);
        assert_eq!(size_of::<Bija3>(), 1);
        assert_eq!(size_of::<CoreD4>(), 1);
        assert_eq!(size_of::<CoreD5>(), 1);
        assert_eq!(size_of::<CoreD6>(), 1);
        assert_eq!(size_of::<SoundD7>(), 1);
        assert_eq!(size_of::<CoreD8>(), 1);
        assert_eq!(size_of::<CoreD9>(), 2);
    }

    
}
