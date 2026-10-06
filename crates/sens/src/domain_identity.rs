//! Exact width-qualified identity carrier for the W1→W8 ladder.
//!
//! Semantic ratification and callable Core-operation identity are deliberately
//! separate. Width never grants a semantic role by itself.
//!
//! - D1-D9 мають чинну семантичну authority згідно з Contract 11.8.
//! - D5 #3305, D6 #3393, D7 #3572, D8 #3960, D9 #4008.
//! - Цей Rust carrier поки матеріалізує лише W1-W8; D9 fail-closed до W9 cut.
//! - Semantic residency і callable/mechanism admission лишаються окремими фактами;
//!   відсутній механізм може fail-closed навіть для ратифікованого resident.
//! - D7 is Sound7/local-ordinal identity and never enters callable routing by width.
//! - D8 exact identity is current; historical Sens8/Sid8 remains compatibility/provenance only.

use crate::{
    Bija3, BinarySourceWord, CoreD4, CoreD5, CoreD6, CoreD8, PredicateBit, Racana2, SoundD7,
};
use std::fmt;

#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum DomainIdentity {
    D1(PredicateBit),
    D2(Racana2),
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    D7(SoundD7),
    D8(CoreD8),
}

impl DomainIdentity {
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

    /// Total lift from the canonical exact-width source layer.
    pub const fn from_source_word(source: BinarySourceWord) -> Self {
        match source {
            BinarySourceWord::W1(word) => Self::D1(PredicateBit::from_word(word)),
            BinarySourceWord::W2(word) => Self::D2(Racana2::from_word(word)),
            BinarySourceWord::W3(word) => Self::D3(Bija3::from_word(word)),
            BinarySourceWord::W4(word) => Self::D4(CoreD4::from_word(word)),
            BinarySourceWord::W5(word) => Self::D5(CoreD5::from_word(word)),
            BinarySourceWord::W6(word) => Self::D6(CoreD6::from_word(word)),
            BinarySourceWord::W7(word) => Self::D7(SoundD7::from_word(word)),
            BinarySourceWord::W8(word) => Self::D8(CoreD8::from_word(word)),
        }
    }

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

    /// Explicit callable/Core-operation projection.
    ///
    /// Це projection саме до callable/mechanism routing, а не реєстр
    /// семантичної residency.
    ///
    /// D3/D4/D5 зараз мають admitted Core-operation projection. D6 є
    /// OWNER-RATIFIED 64/64 під #3393, але на цій межі ще не має загального
    /// callable projection: відсутній механізм лишається fail-closed і не
    /// скасовує D6 semantic identity. D8 так само OWNER-RATIFIED #3960.
    /// D9 OWNER-RATIFIED #4008, але цей W1-W8 carrier ще не матеріалізує D9;
    /// відсутній W9/mechanism support fail-closed і не скасовує D9 residency.
    pub const fn core_operation(self) -> Option<CoreDomainIdentity> {
        match self {
            Self::D3(value) => Some(CoreDomainIdentity::D3(value)),
            Self::D4(value) => Some(CoreDomainIdentity::D4(value)),
            Self::D5(value) => Some(CoreDomainIdentity::D5(value)),
            Self::D1(_) | Self::D2(_) | Self::D6(_) | Self::D7(_) | Self::D8(_) => None,
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

/// Callable/Core-operation identity. This is intentionally not the universal
/// domain identity type.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CoreDomainIdentity {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    D8(CoreD8),
}

impl CoreDomainIdentity {
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::D8(_) => 8,
        }
    }

    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
            Self::D8(value) => value.word().packed_bits(),
        }
    }

    pub const fn from_source_word(source: BinarySourceWord) -> Option<Self> {
        DomainIdentity::from_source_word(source).core_operation()
    }

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

impl From<PredicateBit> for DomainIdentity {
    fn from(value: PredicateBit) -> Self { Self::D1(value) }
}
impl From<Racana2> for DomainIdentity {
    fn from(value: Racana2) -> Self { Self::D2(value) }
}
impl From<Bija3> for DomainIdentity {
    fn from(value: Bija3) -> Self { Self::D3(value) }
}
impl From<CoreD4> for DomainIdentity {
    fn from(value: CoreD4) -> Self { Self::D4(value) }
}
impl From<CoreD5> for DomainIdentity {
    fn from(value: CoreD5) -> Self { Self::D5(value) }
}
impl From<CoreD6> for DomainIdentity {
    fn from(value: CoreD6) -> Self { Self::D6(value) }
}
impl From<SoundD7> for DomainIdentity {
    fn from(value: SoundD7) -> Self { Self::D7(value) }
}
impl From<CoreD8> for DomainIdentity {
    fn from(value: CoreD8) -> Self { Self::D8(value) }
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
impl From<CoreD8> for CoreDomainIdentity {
    fn from(value: CoreD8) -> Self { Self::D8(value) }
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
    fn all_d1_d8_source_words_round_trip_through_domain_identity() {
        for raw in 0..=1 {
            let source = BinarySourceWord::W1(Bit1::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
        for raw in 0..=3 {
            let source = BinarySourceWord::W2(Bit2::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
        for raw in 0..=7 {
            let source = BinarySourceWord::W3(Bit3::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
        for raw in 0..=15 {
            let source = BinarySourceWord::W4(Bit4::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
        for raw in 0..=31 {
            let source = BinarySourceWord::W5(Bit5::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
        for raw in 0..=63 {
            let source = BinarySourceWord::W6(Bit6::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
        for raw in 0..=127 {
            let source = BinarySourceWord::W7(Bit7::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
        for raw in 0..=255 {
            let source = BinarySourceWord::W8(Bit8::new(raw).unwrap());
            assert_eq!(DomainIdentity::from_source_word(source).source_word(), source);
        }
    }

    #[test]
    fn callable_projection_separates_current_d6_identity_from_missing_generic_mechanism() {
        for source in [
            BinarySourceWord::W1(Bit1::new(1).unwrap()),
            BinarySourceWord::W2(Bit2::new(1).unwrap()),
            BinarySourceWord::W7(Bit7::new(1).unwrap()),
            BinarySourceWord::W8(Bit8::new(1).unwrap()),
        ] {
            assert!(DomainIdentity::from_source_word(source).core_operation().is_none());
        }

        // Contract 11.8 / #3393: D6 semantic identity is current.
        // Водночас generic callable mechanism для D6 тут навмисно не
        // приписується автоматично: semantic residency != mechanism admission.
        let d6_word = Bit6::new(1).unwrap();
        let d6_domain = DomainIdentity::from_source_word(BinarySourceWord::W6(d6_word));
        assert!(matches!(d6_domain, DomainIdentity::D6(_)));
        assert!(d6_domain.core_operation().is_none());
        let d6_identity = CoreDomainIdentity::D6(CoreD6::from_word(d6_word));
        assert_eq!((d6_identity.width(), d6_identity.packed_bits()), (6, 1));

        let d3 = DomainIdentity::from_source_word(
            BinarySourceWord::W3(Bit3::new(1).unwrap())
        ).core_operation().unwrap();
        assert_eq!((d3.width(), d3.packed_bits()), (3, 1));

        let d4 = DomainIdentity::from_source_word(
            BinarySourceWord::W4(Bit4::new(1).unwrap())
        ).core_operation().unwrap();
        assert_eq!((d4.width(), d4.packed_bits()), (4, 1));

        let d5 = DomainIdentity::from_source_word(
            BinarySourceWord::W5(Bit5::new(1).unwrap())
        ).core_operation().unwrap();
        assert_eq!((d5.width(), d5.packed_bits()), (5, 1));
    }

    #[test]
    fn equal_payloads_do_not_collapse_across_d1_d8() {
        let ids = [
            DomainIdentity::from_source_word(BinarySourceWord::W1(Bit1::new(1).unwrap())),
            DomainIdentity::from_source_word(BinarySourceWord::W2(Bit2::new(1).unwrap())),
            DomainIdentity::from_source_word(BinarySourceWord::W3(Bit3::new(1).unwrap())),
            DomainIdentity::from_source_word(BinarySourceWord::W4(Bit4::new(1).unwrap())),
            DomainIdentity::from_source_word(BinarySourceWord::W5(Bit5::new(1).unwrap())),
            DomainIdentity::from_source_word(BinarySourceWord::W6(Bit6::new(1).unwrap())),
            DomainIdentity::from_source_word(BinarySourceWord::W7(Bit7::new(1).unwrap())),
            DomainIdentity::from_source_word(BinarySourceWord::W8(Bit8::new(1).unwrap())),
        ];
        for id in ids { assert_eq!(id.packed_bits(), 1); }
        for left in 0..ids.len() {
            for right in left + 1..ids.len() {
                assert_ne!(ids[left], ids[right]);
            }
        }
    }
}
