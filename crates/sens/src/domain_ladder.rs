//! Механічна драбина D1–D10 без жодної Rust-семантики.
//!
//! Координата — рівно (ширина, біти). Значення, назви, закони,
//! допуск до виконання та оракули належать доменним джерелам SENS.
//! Це НЕ другий реєстр функцій і НЕ дозвіл на виконання D10.
//!
//! Аксіома бітності: ширина ключа = адреса домену. D*n* ніколи не
//! приймає ключ іншої довжини. Рівний packed payload у різних ширинах
//! — різні координати.
//!
//! D7 v2: 128/128 точних клавіатурних координат з
//! `knowledge/d7-keyboard-v2-ratified.json`, усі лише Text/Data.
//! Історична D7 v1 (126/128) не є поточною владою координат.
//! Зайнятість комірки ≠ дозвіл викликати функцію.

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

    /// Pure occupancy projection from owner-ratified domain sources.
    ///
    /// D3–D7 are a generated coordinate subset. D8/D9 have independent
    /// full-width owner certificates; Contract 11.9 separately ratifies
    /// D10 as one complete 1024/1024 domain, without runtime admission.
    /// D1/D2 structural/predicate roles stay unprojected.
    /// Some(true) proves occupancy, never a callable mechanism or human name.
    ///
    /// D7 v2: every one of 128 W7 text/data coordinates is occupied.
    /// Occupancy alone cannot mint a callable mechanism.
    pub fn owner_residency(self) -> Option<bool> {
        if self.width == 10 {
            // Whole-domain ratification; NOT physical T5 or callability.
            return Some(true);
        }
        if crate::domain_owner_generated::DOMAIN_OWNER_FULL_WIDTHS.contains(&self.width) {
            return Some(true);
        }
        if !(3..=7).contains(&self.width) {
            return None;
        }
        let mask = crate::domain_owner_generated::DOMAIN_OWNER_BITMAPS
            .iter()
            .find(|mask| mask.width == self.width)?;
        let slot = usize::from(self.bits / 64);
        Some(((mask.slots[slot] >> (self.bits % 64)) & 1) != 0)
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

    /// Вичерпний свідок точності: усі W7 = 128/128 data-only;
    /// помилкове розширення до восьмого біта й callable неприпустимі.
    #[test]
    fn d7_keyboard_v2_exhaustive_width_and_noncallability() {
        let mut seen = 0usize;
        for bits in 0..128u16 {
            let coordinate = DomainCoordinate::new(7, bits).expect("exact W7");
            assert_eq!(coordinate.width(), 7);
            assert_eq!(coordinate.bits(), bits);
            assert_eq!(coordinate.owner_residency(), Some(true));
            let typed = crate::DomainIdentity::from_source_word(
                crate::BinarySourceWord::W7(
                    crate::Bit7::new(bits as u8).expect("seven-bit word"),
                ),
            );
            assert_eq!(typed.width(), 7);
            assert_eq!(typed.packed_bits(), bits);
            assert!(typed.core_operation().is_none(), "D7 must never be callable");
            assert_ne!(coordinate, DomainCoordinate::new(8, bits).unwrap());
            seen += 1;
        }
        assert_eq!(seen, 128);
        assert_eq!(DomainCoordinate::new(7, 128), None);
        assert!(crate::Bit7::new(128).is_none());
        // Старий v1-резерв тепер є W7-текстом, але не функцією.
        for bits in [0b0100001, 0b0101010] {
            assert_eq!(DomainCoordinate::new(7, bits).unwrap().owner_residency(), Some(true));
            assert_ne!(DomainCoordinate::new(7, bits), DomainCoordinate::new(8, bits));
        }
        assert_ne!(DomainCoordinate::new(6, 33), DomainCoordinate::new(7, 33));
    }

    #[test]
    fn d8_d9_all_coordinates_are_owner_residents_without_becoming_executable() {
        for (width, population) in [(8u8, 256u16), (9u8, 512u16)] {
            for bits in 0..population {
                let resident = DomainCoordinate::new(width, bits).unwrap();
                assert_eq!(resident.owner_residency(), Some(true));
                assert_ne!(resident, DomainCoordinate::new(10, bits).unwrap());
            }
        }
        for bits in [0, 1, 255, 511, 1023] {
            assert_eq!(
                DomainCoordinate::new(10, bits).unwrap().owner_residency(),
                Some(true),
                "whole D10 owner ratification is not an execution admission"
            );
        }
    }

    #[test]
    fn d10_stays_exactly_ten_bits_with_no_callable_projection() {
        assert_eq!(DomainCoordinate::new(10, 1023).unwrap().bits(), 1023);
        assert_eq!(DomainCoordinate::new(10, 1024), None);
        assert_ne!(DomainCoordinate::new(9, 511), DomainCoordinate::new(10, 511));
        for bits in 0..1024 {
            assert_eq!(DomainCoordinate::new(10, bits).unwrap().owner_residency(), Some(true));
        }
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
