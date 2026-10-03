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

use crate::bits::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6};
use std::fmt;

/// Exact one-bit carrier for the SENS predicate-result domain.
///
/// The mapping/orientation of the bit is language-owned and deliberately absent
/// here. In particular, there is no `bool` constructor or conversion.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct PredicateBit(Bit1);

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


/// Exact four-bit carrier for the ratified Core.D4 bootstrap domain.
///
/// This type proves only exact Core.D4 membership. The occupied/free map and
/// executable laws remain owned by #2169 and SENS conformance evidence.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD4(Bit4);

impl CoreD4 {
    /// Wrap an already validated four-bit word as a Core.D4 member.
    pub const fn from_word(word: Bit4) -> Self {
        Self(word)
    }

    /// Recover the mechanical four-bit word without interpreting it.
    pub const fn word(self) -> Bit4 {
        self.0
    }
}


/// Exact five-bit carrier for the ratified Core.D5 domain.
///
/// This proves domain membership only. Individual D5 coordinate meanings are
/// owned by the SENS owner map/laws, not by this Rust representation type.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD5(Bit5);

impl CoreD5 {
    /// Wrap an already validated five-bit word as a Core.D5 member.
    pub const fn from_word(word: Bit5) -> Self {
        Self(word)
    }

    /// Recover the mechanical five-bit word without interpreting it.
    pub const fn word(self) -> Bit5 {
        self.0
    }
}

/// Exact six-bit carrier for the ratified Core.D6 domain.
///
/// This proves domain membership only. It deliberately has no implicit
/// relationship to Core.D5 or Sens8 identity.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct CoreD6(Bit6);

impl CoreD6 {
    /// Wrap an already validated six-bit word as a Core.D6 member.
    pub const fn from_word(word: Bit6) -> Self {
        Self(word)
    }

    /// Recover the mechanical six-bit word without interpreting it.
    pub const fn word(self) -> Bit6 {
        self.0
    }
}


/// Explicit compatibility wrapper for the historical exact-eight-bit carrier.
///
/// This exists only while old transport/backend paths are being migrated. It
/// never compares equal to a domain-qualified callable merely from packed bits.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct LegacySens8(crate::Sens8);

impl LegacySens8 {
    pub const fn from_sens8(value: crate::Sens8) -> Self {
        Self(value)
    }

    pub const fn sens8(self) -> crate::Sens8 {
        self.0
    }
}

/// Domain-qualified callable identity for the Core D3..D6 strata.
///
/// The variant is part of identity. This is a carrier, not a table of
/// operation meanings: laws/owner maps still decide whether a coordinate is
/// executable. D1, D2 and D7 are deliberately absent.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableDomainId {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    Legacy8(LegacySens8),
}

impl CallableDomainId {
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::Legacy8(_) => 8,
        }
    }

    /// Mechanical bits only; callers must keep the domain/compatibility variant.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(word) => word.word().packed_bits(),
            Self::D4(word) => word.word().packed_bits(),
            Self::D5(word) => word.word().packed_bits(),
            Self::D6(word) => word.word().packed_bits(),
            Self::Legacy8(word) => word.sens8().packed_byte(),
        }
    }

    /// Construct only admitted callable Core widths. Width 1/2/7/8 is not
    /// promoted by representation alone.
    pub const fn from_domain_bits(width: usize, payload: u8) -> Option<Self> {
        match width {
            3 => match Bit3::new(payload) {
                Some(word) => Some(Self::D3(Bija3::from_word(word))),
                None => None,
            },
            4 => match Bit4::new(payload) {
                Some(word) => Some(Self::D4(CoreD4::from_word(word))),
                None => None,
            },
            5 => match Bit5::new(payload) {
                Some(word) => Some(Self::D5(CoreD5::from_word(word))),
                None => None,
            },
            6 => match Bit6::new(payload) {
                Some(word) => Some(Self::D6(CoreD6::from_word(word))),
                None => None,
            },
            _ => None,
        }
    }

    /// Only the explicitly tagged compatibility variant can recover Sens8.
    pub const fn legacy_sens8(self) -> Option<crate::Sens8> {
        match self {
            Self::Legacy8(word) => Some(word.sens8()),
            Self::D3(_) | Self::D4(_) | Self::D5(_) | Self::D6(_) => None,
        }
    }

    /// Named compatibility entry. Intentionally no implicit From<Sens8>.
    pub const fn from_legacy_sens8(value: crate::Sens8) -> Self {
        Self::Legacy8(LegacySens8::from_sens8(value))
    }
}

impl From<Bija3> for CallableDomainId {
    fn from(value: Bija3) -> Self {
        Self::D3(value)
    }
}

impl From<CoreD4> for CallableDomainId {
    fn from(value: CoreD4) -> Self {
        Self::D4(value)
    }
}

impl From<CoreD5> for CallableDomainId {
    fn from(value: CoreD5) -> Self {
        Self::D5(value)
    }
}

impl From<CoreD6> for CallableDomainId {
    fn from(value: CoreD6) -> Self {
        Self::D6(value)
    }
}

impl fmt::Display for CallableDomainId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{:0width$b}",
            self.packed_bits(),
            width = self.width()
        )
    }
}

impl fmt::Debug for CallableDomainId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::D3(_) => write!(formatter, "CallableDomainId::D3({self})"),
            Self::D4(_) => write!(formatter, "CallableDomainId::D4({self})"),
            Self::D5(_) => write!(formatter, "CallableDomainId::D5({self})"),
            Self::D6(_) => write!(formatter, "CallableDomainId::D6({self})"),
            Self::Legacy8(_) => write!(formatter, "CallableDomainId::Legacy8({self})"),
        }
    }
}

impl fmt::Debug for LegacySens8 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "LegacySens8({})", self.0)
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
    }

    #[test]
    fn callable_domain_identity_never_collapses_equal_payloads() {
        let d3 = CallableDomainId::D3(Bija3::from_word(Bit3::new(1).unwrap()));
        let d4 = CallableDomainId::D4(CoreD4::from_word(Bit4::new(1).unwrap()));
        let d5 = CallableDomainId::D5(CoreD5::from_word(Bit5::new(1).unwrap()));
        let d6 = CallableDomainId::D6(CoreD6::from_word(Bit6::new(1).unwrap()));
        let legacy =
            CallableDomainId::from_legacy_sens8(crate::Sens8::__from_macro_bits("00000001"));

        for id in [d3, d4, d5, d6, legacy] {
            assert_eq!(id.packed_bits(), 1);
        }

        assert_eq!(
            [d3.width(), d4.width(), d5.width(), d6.width(), legacy.width()],
            [3, 4, 5, 6, 8]
        );
        assert!(d3 != d4);
        assert!(d4 != d5);
        assert!(d5 != d6);
        assert!(d3 != legacy);
        assert!(d4 != legacy);
        assert!(d5 != legacy);
        assert!(d6 != legacy);
        assert!(d3.legacy_sens8().is_none());
        assert_eq!(legacy.legacy_sens8().unwrap().packed_byte(), 1);
    }

    #[test]
    fn callable_constructor_admits_only_d3_through_d6() {
        for width in [1usize, 2, 7, 8] {
            assert!(CallableDomainId::from_domain_bits(width, 0).is_none());
        }
        for width in [3usize, 4, 5, 6] {
            let id = CallableDomainId::from_domain_bits(width, 0).unwrap();
            assert_eq!(id.width(), width);
        }
    }

    #[test]
    fn domain_carriers_remain_one_host_byte() {
        assert_eq!(size_of::<PredicateBit>(), 1);
        assert_eq!(size_of::<Racana2>(), 1);
        assert_eq!(size_of::<Bija3>(), 1);
        assert_eq!(size_of::<CoreD4>(), 1);
        assert_eq!(size_of::<CoreD5>(), 1);
        assert_eq!(size_of::<CoreD6>(), 1);
    }
}
