//! Механічна драбина D1–D10 без жодної Rust-семантики.
//!
//! Координата — рівно (ширина, біти). Значення, назви, закони,
//! допуск до виконання та оракули належать доменним джерелам SENS.
//! Це НЕ другий реєстр функцій і НЕ дозвіл на виконання D10.

/// A width-qualified, meaning-free code word in the D1–D10 ladder.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct DomainCoordinate {
    width: u8,
    bits: u16,
}

impl DomainCoordinate {
    /// Fail closed for out-of-range rungs and truncated payloads.
    pub const fn new(width: u8, bits: u16) -> Option<Self> {
        if width == 0 || width > 10 || bits >= (1u16 << width) {
            return None;
        }
        Some(Self { width, bits })
    }

    /// Mechanically project any already-validated D1-D9 source identity.
    /// D7 is an exact W7 coordinate; this grants neither a sound role nor
    /// generic callability. D10 remains representable via `new` only.
    pub const fn from_domain_identity(identity: crate::DomainIdentity) -> Self {
        Self {
            width: identity.width() as u8,
            bits: identity.packed_bits(),
        }
    }

    pub const fn width(self) -> u8 {
        self.width
    }

    pub const fn bits(self) -> u16 {
        self.bits
    }
}

#[cfg(test)]
mod tests {
    use super::DomainCoordinate;

    #[test]
    fn all_rungs_are_width_qualified_without_guessing_meaning() {
        for width in 1..=10 {
            for bits in 0..(1u16 << width) {
                let coordinate = DomainCoordinate::new(width, bits).unwrap();
                assert_eq!(coordinate.width(), width);
                assert_eq!(coordinate.bits(), bits);
            }
            assert_eq!(DomainCoordinate::new(width, 1u16 << width), None);
        }
    }

    #[test]
    fn d10_stays_exactly_ten_bits_with_no_callable_projection() {
        assert_eq!(DomainCoordinate::new(10, 1023).unwrap().bits(), 1023);
        assert_eq!(DomainCoordinate::new(10, 1024), None);
        assert_ne!(DomainCoordinate::new(9, 511), DomainCoordinate::new(10, 511));
        assert_eq!(DomainCoordinate::new(0, 0), None);
        assert_eq!(DomainCoordinate::new(11, 0), None);
    }
    #[test]
    fn every_d7_source_word_has_a_width_preserving_coordinate() {
        use crate::{BinarySourceWord, Bit7, DomainIdentity};

        for bits in 0u8..=127 {
            let word = BinarySourceWord::W7(Bit7::new(bits).unwrap());
            let identity = DomainIdentity::from_source_word(word);
            let coordinate = DomainCoordinate::from_domain_identity(identity);

            assert!(matches!(identity, DomainIdentity::D7(_)));
            assert_eq!(coordinate, DomainCoordinate::new(7, u16::from(bits)).unwrap());
            assert_ne!(coordinate, DomainCoordinate::new(8, u16::from(bits)).unwrap());
        }
    }

}
