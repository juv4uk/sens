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

    /// Pack a D1–D10 sequence as one dense payload, without byte padding
    /// between adjacent domain words. Width comes from each coordinate;
    /// this operation assigns no executable meaning and is not a new codec.
    pub fn pack_sequence(words: &[Self]) -> crate::PackedBitstream {
        let mut packer = crate::BitPacker::new();
        for &word in words {
            packer.push_coordinate(word);
        }
        packer.finish()
    }

    /// Recover words using an external, source-owned width schedule.
    /// Reject invalid widths, truncation and extra meaningful bits.
    /// An unframed byte payload can never determine word boundaries itself.
    pub fn unpack_sequence(
        payload: &crate::PackedBitstream,
        widths: &[u8],
    ) -> Option<Vec<Self>> {
        let mut words = Vec::with_capacity(widths.len());
        let mut offset = 0usize;
        for &width in widths {
            let word = payload.read_coordinate(offset, width)?;
            offset = offset.checked_add(usize::from(width))?;
            words.push(word);
        }
        (offset == payload.bit_len()).then_some(words)
    }

    /// Pure occupancy projection from owner-ratified domain sources.
    ///
    /// D3–D7 are a generated coordinate subset. D8/D9 have independent
    /// full-width owner certificates; Contract 11.9 separately ratifies
    /// D10 as one complete 1024/1024 domain, without runtime admission.
    /// D1/D2 structural/predicate roles stay unprojected.
    /// Some(true) proves occupancy, never a callable mechanism or human name.
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
            Some(true),
            "D8 is separately owner-ratified, not inherited from D7"
        );
        assert_eq!(
            DomainCoordinate::new(10, 0b0100001).unwrap().owner_residency(),
            Some(true)
        );
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


    #[test]
    fn exact_sequence_all_d1_through_d10_words_has_no_internal_padding() {
        let words = (1u8..=10)
            .map(|width| DomainCoordinate::new(width, (1u16 << width) - 1).unwrap())
            .collect::<Vec<_>>();
        let payload = DomainCoordinate::pack_sequence(&words);
        assert_eq!(payload.bit_len(), 55);
        assert_eq!(payload.byte_len(), 7);
        assert_eq!(payload.valid_bits_in_last_byte(), 7);
        assert_eq!(
            DomainCoordinate::unpack_sequence(&payload, &(1u8..=10).collect::<Vec<_>>()),
            Some(words)
        );
        // Independently rounding every word to a byte would cost 12 bytes.
        assert!(payload.byte_len() < 12);
    }

    #[test]
    fn equal_payload_d3_d4_d9_d10_keeps_each_original_width() {
        let widths = [3u8, 4, 9, 10];
        let words = widths.map(|width| DomainCoordinate::new(width, 1).unwrap());
        for word in words {
            assert_eq!(word.bits(), 1);
        }
        for left in 0..words.len() {
            for right in left + 1..words.len() {
                assert_ne!(words[left], words[right]);
            }
        }
        let packed = DomainCoordinate::pack_sequence(&words);
        assert_eq!(packed.bit_len(), 26);
        assert_eq!(packed.byte_len(), 4);
        assert_eq!(DomainCoordinate::unpack_sequence(&packed, &widths), Some(words.to_vec()));
        assert!(DomainCoordinate::unpack_sequence(&packed, &[3, 4, 9, 9]).is_none());
        // A different schedule with the same total length can parse as
        // different valid words: only trusted source grammar owns boundaries.
        assert_ne!(
            DomainCoordinate::unpack_sequence(&packed, &[4, 3, 9, 10]),
            Some(words.to_vec())
        );
    }

    #[test]
    fn all_1024_d10_words_round_trip_after_seven_unaligned_prefix_bits() {
        let prefix = [
            DomainCoordinate::new(3, 0b101).unwrap(),
            DomainCoordinate::new(4, 0b0010).unwrap(),
        ];
        for bits in 0u16..1024 {
            let words = [prefix[0], prefix[1], DomainCoordinate::new(10, bits).unwrap()];
            let packed = DomainCoordinate::pack_sequence(&words);
            assert_eq!(packed.bit_len(), 17);
            assert_eq!(packed.byte_len(), 3);
            assert_eq!(packed.valid_bits_in_last_byte(), 1);
            assert_eq!(packed.read_coordinate(7, 10), Some(words[2]));
            assert_eq!(DomainCoordinate::unpack_sequence(&packed, &[3, 4, 10]), Some(words.to_vec()));
            assert_ne!(words[2], DomainCoordinate::new(9, bits % 512).unwrap());
        }
    }

    #[test]
    fn invalid_width_truncation_extra_tail_and_noncanonical_padding_are_rejected() {
        let words = [
            DomainCoordinate::new(3, 0b101).unwrap(),
            DomainCoordinate::new(10, 0b1111000011).unwrap(),
        ];
        let packed = DomainCoordinate::pack_sequence(&words);
        assert_eq!(packed.bit_len(), 13);
        assert_eq!(DomainCoordinate::unpack_sequence(&packed, &[3, 10]), Some(words.to_vec()));
        let invalid_schedules: &[&[u8]] = &[
            &[], &[3], &[3, 9], &[3, 11], &[0, 3, 10], &[3, 10, 1],
        ];
        for &widths in invalid_schedules {
            assert!(DomainCoordinate::unpack_sequence(&packed, widths).is_none());
        }
        let mut bad_tail = packed.bytes().to_vec();
        *bad_tail.last_mut().unwrap() |= 1;
        assert!(crate::PackedBitstream::from_parts(bad_tail, 13).is_none());
        let mut extra_byte = packed.bytes().to_vec();
        extra_byte.push(0);
        assert!(crate::PackedBitstream::from_parts(extra_byte, 13).is_none());
        let empty = DomainCoordinate::pack_sequence(&[]);
        assert_eq!(empty.bit_len(), 0);
        assert_eq!(empty.byte_len(), 0);
        assert_eq!(DomainCoordinate::unpack_sequence(&empty, &[]), Some(vec![]));
        assert!(DomainCoordinate::unpack_sequence(&empty, &[1]).is_none());
    }

}
