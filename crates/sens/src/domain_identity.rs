//! Domain-qualified identity for the SENS D1-D8 ladder.
//!
//! Width is part of identity, but width alone is not semantic authority.
//! D7 is additionally role-qualified: SoundCell and LocalOrdinal remain
//! distinct even when their seven payload bits are identical.
//!
//! Historical Sens8/Sid8 is not a variant here and cannot be converted into a
//! domain identity implicitly.

use crate::{
    Bija3, BinarySourceWord, CoreD4, CoreD5, CoreD6, CoreD8, D7LocalOrdinal,
    D7SoundCell, PredicateBit, Racana2,
};
use std::fmt;

/// Exact domain-qualified identity for the ratified D1-D8 SENS domains.
///
/// D1/D2 are represented here so runtime/transport code can carry them without
/// widening. They are not automatically callable. D7 requires an explicit
/// semantic role and therefore bare W7 source cannot choose a D7 variant by
/// width alone.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CoreDomainIdentity {
    D1(PredicateBit),
    D2(Racana2),
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    D7Sound(D7SoundCell),
    D7LocalOrdinal(D7LocalOrdinal),
    D8(CoreD8),
}

impl fmt::Debug for CoreDomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::D7Sound(_) => write!(
                formatter,
                "CoreDomainIdentity<D7.SoundCell>({:07b})",
                self.packed_bits()
            ),
            Self::D7LocalOrdinal(_) => write!(
                formatter,
                "CoreDomainIdentity<D7.LocalOrdinal>({:07b})",
                self.packed_bits()
            ),
            _ => {
                let width = self.width();
                write!(
                    formatter,
                    "CoreDomainIdentity<D{width}>({:0width$b})",
                    self.packed_bits()
                )
            }
        }
    }
}

impl fmt::Display for CoreDomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::D7Sound(_) => write!(formatter, "d7.sound/{:07b}", self.packed_bits()),
            Self::D7LocalOrdinal(_) => {
                write!(formatter, "d7.ordinal/{:07b}", self.packed_bits())
            }
            _ => write!(
                formatter,
                "{:0width$b}",
                self.packed_bits(),
                width = self.width()
            ),
        }
    }
}

impl CoreDomainIdentity {
    pub const fn width(self) -> usize {
        match self {
            Self::D1(_) => 1,
            Self::D2(_) => 2,
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::D7Sound(_) | Self::D7LocalOrdinal(_) => 7,
            Self::D8(_) => 8,
        }
    }

    /// Mechanical payload only. The enum variant must remain attached.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D1(value) => value.word().packed_bits(),
            Self::D2(value) => value.word().packed_bits(),
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
            Self::D7Sound(value) => value.word().packed_bits(),
            Self::D7LocalOrdinal(value) => value.word().packed_bits(),
            Self::D8(value) => value.word().packed_bits(),
        }
    }

    /// Direct source-word admission where width uniquely identifies the domain
    /// role used by canonical expression source.
    ///
    /// D1/D2 remain context-owned predicate/structure carriers; W7 is
    /// intentionally ambiguous between SoundCell and LocalOrdinal and therefore
    /// requires an explicit D7 role constructor.
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

    pub const fn d1(value: PredicateBit) -> Self {
        Self::D1(value)
    }

    pub const fn d2(value: Racana2) -> Self {
        Self::D2(value)
    }

    pub const fn d7_sound(value: D7SoundCell) -> Self {
        Self::D7Sound(value)
    }

    pub const fn d7_local_ordinal(value: D7LocalOrdinal) -> Self {
        Self::D7LocalOrdinal(value)
    }

    /// Mechanical exact-width projection. For D7 this does not carry the role;
    /// callers serializing semantic identity must preserve the enum variant too.
    pub const fn source_word(self) -> BinarySourceWord {
        match self {
            Self::D1(value) => BinarySourceWord::W1(value.word()),
            Self::D2(value) => BinarySourceWord::W2(value.word()),
            Self::D3(value) => BinarySourceWord::W3(value.word()),
            Self::D4(value) => BinarySourceWord::W4(value.word()),
            Self::D5(value) => BinarySourceWord::W5(value.word()),
            Self::D6(value) => BinarySourceWord::W6(value.word()),
            Self::D7Sound(value) => BinarySourceWord::W7(value.word()),
            Self::D7LocalOrdinal(value) => BinarySourceWord::W7(value.word()),
            Self::D8(value) => BinarySourceWord::W8(value.word()),
        }
    }
}

impl From<PredicateBit> for CoreDomainIdentity {
    fn from(value: PredicateBit) -> Self { Self::D1(value) }
}
impl From<Racana2> for CoreDomainIdentity {
    fn from(value: Racana2) -> Self { Self::D2(value) }
}
impl From<Bija3> for CoreDomainIdentity {
    fn from(value: Bija3) -> Self { Self::D3(value) }
}
impl From<CoreD4> for CoreDomainIdentity {
    fn from(value: CoreD4) -> Self { Self::D4(value) }
}
impl From<CoreD5> for CoreDomainIdentity {
    fn from(value: CoreD5) -> Self { Self::D5(value) }
}
impl From<CoreD6> for CoreDomainIdentity {
    fn from(value: CoreD6) -> Self { Self::D6(value) }
}
impl From<D7SoundCell> for CoreDomainIdentity {
    fn from(value: D7SoundCell) -> Self { Self::D7Sound(value) }
}
impl From<D7LocalOrdinal> for CoreDomainIdentity {
    fn from(value: D7LocalOrdinal) -> Self { Self::D7LocalOrdinal(value) }
}
impl From<CoreD8> for CoreDomainIdentity {
    fn from(value: CoreD8) -> Self { Self::D8(value) }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8};

    #[test]
    fn direct_source_bridge_preserves_d3_d6_and_d8() {
        for raw in 0..=7 {
            let source = BinarySourceWord::W3(Bit3::new(raw).unwrap());
            assert_eq!(CoreDomainIdentity::from_source_word(source).unwrap().source_word(), source);
        }
        for raw in 0..=15 {
            let source = BinarySourceWord::W4(Bit4::new(raw).unwrap());
            assert_eq!(CoreDomainIdentity::from_source_word(source).unwrap().source_word(), source);
        }
        for raw in 0..=31 {
            let source = BinarySourceWord::W5(Bit5::new(raw).unwrap());
            assert_eq!(CoreDomainIdentity::from_source_word(source).unwrap().source_word(), source);
        }
        for raw in 0..=63 {
            let source = BinarySourceWord::W6(Bit6::new(raw).unwrap());
            assert_eq!(CoreDomainIdentity::from_source_word(source).unwrap().source_word(), source);
        }
        for raw in 0..=255 {
            let source = BinarySourceWord::W8(Bit8::new(raw).unwrap());
            assert_eq!(CoreDomainIdentity::from_source_word(source).unwrap().source_word(), source);
        }
    }

    #[test]
    fn d1_d2_and_d7_require_their_own_context_or_role() {
        assert!(CoreDomainIdentity::from_source_word(BinarySourceWord::W1(Bit1::new(1).unwrap())).is_none());
        assert!(CoreDomainIdentity::from_source_word(BinarySourceWord::W2(Bit2::new(1).unwrap())).is_none());
        assert!(CoreDomainIdentity::from_source_word(BinarySourceWord::W7(Bit7::new(1).unwrap())).is_none());

        let d1 = CoreDomainIdentity::d1(PredicateBit::from_word(Bit1::new(1).unwrap()));
        let d2 = CoreDomainIdentity::d2(Racana2::from_word(Bit2::new(1).unwrap()));
        let sound = CoreDomainIdentity::d7_sound(D7SoundCell::from_word(Bit7::new(1).unwrap()));
        let ordinal = CoreDomainIdentity::d7_local_ordinal(D7LocalOrdinal::from_word(Bit7::new(1).unwrap()));

        assert_eq!(d1.width(), 1);
        assert_eq!(d2.width(), 2);
        assert_eq!(sound.width(), 7);
        assert_eq!(ordinal.width(), 7);
        assert_ne!(sound, ordinal);
    }

    #[test]
    fn equal_payloads_across_all_roles_do_not_collapse() {
        let ids = [
            CoreDomainIdentity::d1(PredicateBit::from_word(Bit1::new(1).unwrap())),
            CoreDomainIdentity::d2(Racana2::from_word(Bit2::new(1).unwrap())),
            CoreDomainIdentity::from(Bija3::from_word(Bit3::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(1).unwrap())),
            CoreDomainIdentity::from(D7SoundCell::from_word(Bit7::new(1).unwrap())),
            CoreDomainIdentity::from(D7LocalOrdinal::from_word(Bit7::new(1).unwrap())),
            CoreDomainIdentity::from(CoreD8::from_word(Bit8::new(1).unwrap())),
        ];
        assert!(ids.iter().all(|id| id.packed_bits() == 1));
        for left in 0..ids.len() {
            for right in left + 1..ids.len() {
                assert_ne!(ids[left], ids[right]);
            }
        }
    }

    #[test]
    fn every_d8_payload_is_preserved_without_sens8_projection() {
        for raw in 0..=255 {
            let id = CoreDomainIdentity::from(CoreD8::from_word(Bit8::new(raw).unwrap()));
            assert_eq!(id.width(), 8);
            assert_eq!(id.packed_bits(), raw);
            assert!(matches!(id, CoreDomainIdentity::D8(_)));
        }
    }
}
