//! Typed representation for the exact domain identities currently modeled here.
//! Numeric D24+ values travel as `BinaryNumber`/`ExactDomainWord::Number`.
//!
//! Semantic ratification and callable Core-operation identity are deliberately
//! separate. Width never grants a semantic role by itself.
//!
//! - Domain identity, resident law, mechanism admission and physical encoding are independent.
//! - Numeric D24/D48/D96/D192/... identity is explicit in the numeric value itself.
//! - The bounded small-word adapter below is not the D1–24+ domain ladder.
//! - No width alone creates semantic identity or callability.
//! - Semantic residency і callable/mechanism admission лишаються окремими фактами;
//!   відсутній механізм може fail-closed навіть для ратифікованого resident.
//! - D7 is keyboard/v2 W7 data identity and never enters callable routing by width.
//! - D8 exact identity is current; a packed transport byte never establishes its domain.

use crate::{
    Bija3, BinarySourceWord, CoreD4, CoreD5, CoreD6, CoreD8, CoreD9, D7DataWord, PredicateBit,
    Racana2,
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
    D7(D7DataWord),
    D8(CoreD8),
    D9(CoreD9),
    /// Exact D10 identity. A callable mechanism requires an explicit,
    /// exact-word runtime admission (for example, a concrete Core4 definition
    /// or a narrowly registered native mechanism); residency alone is not enough.
    D10(crate::DomainD10),
}

impl DomainIdentity {
    pub const fn width(self) -> usize {
        match self {
            Self::D10(value) => value.coordinate().width() as usize,
            _ => self.source_word().width(),
        }
    }

    /// Mechanical payload wide enough for every current exact domain.
    ///
    /// Width remains part of `DomainIdentity`; the numeric payload alone is
    /// never a semantic identity.
    pub const fn packed_bits(self) -> u16 {
        match self {
            Self::D1(value) => value.word().packed_bits() as u16,
            Self::D2(value) => value.word().packed_bits() as u16,
            Self::D3(value) => value.word().packed_bits() as u16,
            Self::D4(value) => value.word().packed_bits() as u16,
            Self::D5(value) => value.word().packed_bits() as u16,
            Self::D6(value) => value.word().packed_bits() as u16,
            Self::D7(value) => value.word().packed_bits() as u16,
            Self::D8(value) => value.word().packed_bits() as u16,
            Self::D9(value) => value.word().packed_bits(),
            Self::D10(value) => value.packed_bits(),
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
            BinarySourceWord::W7(word) => Self::D7(D7DataWord::from_word(word)),
            BinarySourceWord::W8(word) => Self::D8(CoreD8::from_word(word)),
            BinarySourceWord::W9(word) => Self::D9(CoreD9::from_word(word)),
        }
    }

    /// Lift an exact domain-ladder coordinate, including D10, without
    /// inferring meaning or callability from width.
    pub fn from_coordinate(coordinate: crate::domain_ladder::DomainCoordinate) -> Self {
        match coordinate.width() {
            10 => {
                Self::D10(crate::DomainD10::new(coordinate.bits()).expect("valid D10 coordinate"))
            }
            1..=9 => Self::from_source_word(coordinate.source_word().expect("D1-D9 coordinate")),
            _ => panic!("unsupported domain identity coordinate"),
        }
    }

    pub const fn coordinate(self) -> crate::domain_ladder::DomainCoordinate {
        crate::domain_ladder::DomainCoordinate::from_domain_identity(self)
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
            Self::D9(value) => BinarySourceWord::W9(value.word()),
            Self::D10(_) => panic!("D10 has no D1-D9 BinarySourceWord representation"),
        }
    }

    /// Explicit callable/Core-operation projection.
    ///
    /// Це projection саме до callable/mechanism routing, а не реєстр
    /// семантичної residency.
    ///
    /// D3/D4/D5 мають admitted Core-operation projection. D6 є OWNER-RATIFIED
    /// 64/64 під #3393; окремі чинні механізми — D6:001110 ADD1,
    /// D6:001111 SUB1, D6:010010 NEG (0 - x) та D6:111110 INTEGERP.
    /// Інші D6 residents лишаються fail-closed; residency не дорівнює mechanism.
    /// D8 так само OWNER-RATIFIED #3960.
    /// D9 OWNER-RATIFIED #4008: direct string mechanisms and the proven
    /// CAR/CDR selector family are callable. Unrelated residents fail closed.
    /// D7 is text data, not a selector rung.
    pub const fn core_operation(self) -> Option<CoreDomainIdentity> {
        match self {
            Self::D3(value) => Some(CoreDomainIdentity::D3(value)),
            Self::D4(value) => Some(CoreDomainIdentity::D4(value)),
            Self::D5(value) => Some(CoreDomainIdentity::D5(value)),
            Self::D6(value)
                if matches!(
                    value.word().packed_bits(),
                    0b001110 | 0b001111 | 0b010010 | 0b111110
                ) =>
            {
                Some(CoreDomainIdentity::D6(value))
            }
            Self::D8(value)
                if matches!(
                    value.word().packed_bits(),
                    0b00000000
                        | 0b00101100
                        | 0b11100000
                        | 0b11101010
                        | 0b11101101
                        | 0b11101110
                        | 0b11110100
                        | 0b11110111
                ) =>
            {
                // Exact D8 CODE-CHAR and MOD use their concrete mechanisms;
                // only listed D8 identities project here. Residency alone
                // never grants callability to any other D8 coordinate.
                Some(CoreDomainIdentity::D8(value))
            }
            Self::D9(value)
                if matches!(
                    value.word().packed_bits(),
                    0b110011110
                        | 0b110011100
                        | 0b110011101
                        | 0b110101010
                        | 0b110101011
                        | 0b110100110
                        | 0b110101001
                ) =>
            {
                Some(CoreDomainIdentity::D9(value))
            }
            // The ratified selector family is a proof of one exact
            // callable mechanism, not a blanket admission of D8/D9.
            Self::D8(value) if matches!(value.word().packed_bits() >> 5, 0b011 | 0b100) => {
                Some(CoreDomainIdentity::D8(value))
            }
            Self::D9(value) if matches!(value.word().packed_bits() >> 6, 0b011 | 0b100) => {
                Some(CoreDomainIdentity::D9(value))
            }
            Self::D9(_) => None,
            Self::D1(_) | Self::D2(_) | Self::D6(_) | Self::D7(_) | Self::D8(_) | Self::D10(_) => {
                None
            }
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
    D9(CoreD9),
}

impl CoreDomainIdentity {
    pub const fn width(self) -> usize {
        self.source_word().width()
    }

    pub const fn packed_bits(self) -> u16 {
        match self {
            Self::D3(value) => value.word().packed_bits() as u16,
            Self::D4(value) => value.word().packed_bits() as u16,
            Self::D5(value) => value.word().packed_bits() as u16,
            Self::D6(value) => value.word().packed_bits() as u16,
            Self::D8(value) => value.word().packed_bits() as u16,
            Self::D9(value) => value.word().packed_bits(),
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
            Self::D9(value) => BinarySourceWord::W9(value.word()),
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
    fn from(value: PredicateBit) -> Self {
        Self::D1(value)
    }
}
impl From<Racana2> for DomainIdentity {
    fn from(value: Racana2) -> Self {
        Self::D2(value)
    }
}
impl From<Bija3> for DomainIdentity {
    fn from(value: Bija3) -> Self {
        Self::D3(value)
    }
}
impl From<CoreD4> for DomainIdentity {
    fn from(value: CoreD4) -> Self {
        Self::D4(value)
    }
}
impl From<CoreD5> for DomainIdentity {
    fn from(value: CoreD5) -> Self {
        Self::D5(value)
    }
}
impl From<CoreD6> for DomainIdentity {
    fn from(value: CoreD6) -> Self {
        Self::D6(value)
    }
}
impl From<D7DataWord> for DomainIdentity {
    fn from(value: D7DataWord) -> Self {
        Self::D7(value)
    }
}
impl From<CoreD8> for DomainIdentity {
    fn from(value: CoreD8) -> Self {
        Self::D8(value)
    }
}
impl From<CoreD9> for DomainIdentity {
    fn from(value: CoreD9) -> Self {
        Self::D9(value)
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
impl From<CoreD9> for CoreDomainIdentity {
    fn from(value: CoreD9) -> Self {
        Self::D9(value)
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
            CoreDomainIdentity::D9(word) => Self::D9(word),
        }
    }
}
