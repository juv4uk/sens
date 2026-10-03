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
/// This proves domain membership only. The D4 owner map decides which
/// coordinates are occupied or reserved; this representation never derives
/// semantics from the packed nibble.
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

/// Width-preserving sum of the currently ratified Core domains D1..D6.
///
/// This is a representation carrier, not an executability claim: a resident
/// may still be reserved, derived, or unavailable to the evaluator. Keeping
/// the domain variant attached prevents equal packed payloads at different
/// widths from collapsing into one identity.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum DomainWord {
    D1(PredicateBit),
    D2(Racana2),
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
}

impl DomainWord {
    /// Exact domain width carried by this value.
    pub const fn width(self) -> usize {
        match self {
            Self::D1(_) => 1,
            Self::D2(_) => 2,
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
        }
    }

    /// Mechanical payload. It is never a standalone semantic identity.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D1(word) => word.word().packed_bits(),
            Self::D2(word) => word.word().packed_bits(),
            Self::D3(word) => word.word().packed_bits(),
            Self::D4(word) => word.word().packed_bits(),
            Self::D5(word) => word.word().packed_bits(),
            Self::D6(word) => word.word().packed_bits(),
        }
    }
}


/// Explicit compatibility wrapper for the historical exact-eight-bit semantic
/// carrier.
///
/// This type exists only so staged migration can keep old backend/transport
/// paths compiling while canonical runtime identity moves to domain-qualified
/// words. It is intentionally not interchangeable with D3/D4/D5/D6 values.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct LegacySens8(crate::Sens8);

impl LegacySens8 {
    /// Wrap an already-existing historical Sens8 value explicitly.
    pub const fn from_sens8(value: crate::Sens8) -> Self {
        Self(value)
    }

    /// Recover the historical compatibility value.
    pub const fn sens8(self) -> crate::Sens8 {
        self.0
    }
}

/// Canonical callable identity during the Sens8-exit migration.
///
/// Width alone is not enough: the domain variant is part of identity. D1
/// predicate answers and D2 structure are deliberately absent because they are
/// not callable merely by being binary.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableDomainId {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    Legacy8(LegacySens8),
}

impl CallableDomainId {
    /// Exact binary width carried by this callable identity.
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::Legacy8(_) => 8,
        }
    }

    /// Mechanical payload only. Domain/compatibility variant remains required
    /// for semantic identity.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(word) => word.word().packed_bits(),
            Self::D4(word) => word.word().packed_bits(),
            Self::D5(word) => word.word().packed_bits(),
            Self::D6(word) => word.word().packed_bits(),
            Self::Legacy8(word) => word.sens8().packed_byte(),
        }
    }

    /// Explicitly recover the historical exact-8 compatibility projection.
    /// Canonical domain-qualified identities never auto-project here.
    pub const fn legacy_sens8(self) -> Option<crate::Sens8> {
        match self {
            Self::Legacy8(word) => Some(word.sens8()),
            Self::D3(_) | Self::D4(_) | Self::D5(_) | Self::D6(_) => None,
        }
    }

    /// Construct the compatibility variant from historical Sens8.
    ///
    /// Kept as a named operation instead of implementing `From<Sens8>` so
    /// compatibility entry is visible at every call site during migration.
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
    fn same_payload_in_different_domains_never_collapses() {
        let d1 = DomainWord::D1(PredicateBit::from_word(Bit1::new(1).unwrap()));
        let d2 = DomainWord::D2(Racana2::from_word(Bit2::new(1).unwrap()));
        let d3 = DomainWord::D3(Bija3::from_word(Bit3::new(1).unwrap()));
        let d4 = DomainWord::D4(CoreD4::from_word(Bit4::new(1).unwrap()));
        let d5 = DomainWord::D5(CoreD5::from_word(Bit5::new(1).unwrap()));
        let d6 = DomainWord::D6(CoreD6::from_word(Bit6::new(1).unwrap()));

        for word in [d1, d2, d3, d4, d5, d6] {
            assert_eq!(word.packed_bits(), 1);
        }
        assert_eq!([d1.width(), d2.width(), d3.width(), d4.width(), d5.width(), d6.width()],
                   [1, 2, 3, 4, 5, 6]);
        assert!(d1 != d2);
        assert!(d2 != d3);
        assert!(d3 != d4);
        assert!(d4 != d5);
        assert!(d5 != d6);
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

        assert_eq!([d3.width(), d4.width(), d5.width(), d6.width(), legacy.width()],
                   [3, 4, 5, 6, 8]);
        assert!(d3 != d4);
        assert!(d4 != d5);
        assert!(d5 != d6);
        assert!(d3 != legacy);
        assert!(d4 != legacy);
        assert_eq!(legacy.legacy_sens8().unwrap().packed_byte(), 1);
        assert!(d3.legacy_sens8().is_none());
        assert!(d4.legacy_sens8().is_none());
        assert!(d5.legacy_sens8().is_none());
        assert!(d6.legacy_sens8().is_none());
    }

    #[test]
    fn callable_domain_identity_excludes_d1_and_d2_by_construction() {
        // There are intentionally no D1/D2 variants on CallableDomainId.
        // This runtime assertion pins the admitted variant widths so a future
        // accidental callable promotion becomes a deliberate test change.
        let widths = [
            CallableDomainId::D3(Bija3::from_word(Bit3::new(0).unwrap())).width(),
            CallableDomainId::D4(CoreD4::from_word(Bit4::new(0).unwrap())).width(),
            CallableDomainId::D5(CoreD5::from_word(Bit5::new(0).unwrap())).width(),
            CallableDomainId::D6(CoreD6::from_word(Bit6::new(0).unwrap())).width(),
        ];
        assert_eq!(widths, [3, 4, 5, 6]);
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
