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

    pub const fn width(self) -> u8 {
        self.width
    }

    pub const fn bits(self) -> u16 {
        self.bits
    }

    /// Pure occupancy projection from owner-ratified domain sources.
    ///
    /// Only D3–D7 have entries in the current generated owner-coordinate
    /// projection. None means "not projected", never "unratified".
    /// Some(true) grants a resident coordinate, never executable callability
    /// or an inferred Sound7/Text7/ordinal role.
    pub fn owner_residency(self) -> Option<bool> {
        if !(3..=7).contains(&self.width) {
            return None;
        }
        Some(
            crate::domain_owner_generated::DOMAIN_OWNER_COORDINATES
                .iter()
                .any(|row| row.width == self.width && u16::from(row.bits) == self.bits),
        )
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
    fn d7_is_admitted_from_owner_rows_only_and_never_from_width_alone() {
        let mut admitted = 0usize;
        for bits in 0..128u16 {
            let coordinate = DomainCoordinate::new(7, bits).expect("exact W7");
            let admission = coordinate.owner_residency().expect("D7 has owner rows");
            assert_eq!(
                admission,
                bits != 0b0100001 && bits != 0b0101010,
                "owner-reserved D7 words must stay unassigned"
            );
            admitted += usize::from(admission);
            let typed = crate::DomainIdentity::from_source_word(
                crate::BinarySourceWord::W7(
                    crate::Bit7::new(bits as u8).expect("seven-bit word"),
                ),
            );
            assert_eq!(typed.width(), 7);
            assert_eq!(typed.packed_bits(), bits);
            assert!(typed.core_operation().is_none(), "D7 residency is not callability");
        }
        assert_eq!(admitted, 126);
        // Width or equal payload in another domain must not inherit D7 occupancy.
        assert_ne!(
            DomainCoordinate::new(6, 0b0100001).unwrap(),
            DomainCoordinate::new(7, 0b0100001).unwrap(),
            "same payload in D6 and D7 is not the same coordinate"
        );
        assert_eq!(
            DomainCoordinate::new(8, 0b0100001).unwrap().owner_residency(),
            None
        );
        assert_eq!(
            DomainCoordinate::new(10, 0b0100001).unwrap().owner_residency(),
            None
        );
    }

    #[test]
    fn d10_stays_exactly_ten_bits_with_no_callable_projection() {
        assert_eq!(DomainCoordinate::new(10, 1023).unwrap().bits(), 1023);
        assert_eq!(DomainCoordinate::new(10, 1024), None);
        assert_ne!(DomainCoordinate::new(9, 511), DomainCoordinate::new(10, 511));
        assert_eq!(DomainCoordinate::new(0, 0), None);
        assert_eq!(DomainCoordinate::new(11, 0), None);
    }
}
