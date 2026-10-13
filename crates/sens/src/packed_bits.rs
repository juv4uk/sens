//! Dense sequential packing for exact-width small SENS words.
//!
//! This module is mechanical transport/storage infrastructure only. It packs
//! already-typed `Bits<N>` values into one continuous MSB-first bitstream.
//! Semantic word order is preserved, but physical byte boundaries are ignored:
//! a word may begin in one byte and end in the next.
//!
//! The packed payload stores only bytes plus the exact number of valid bits.
//! It does not assign SENS meaning, encode semantic word boundaries, or choose
//! a wire representation for the bit length. Those framing concerns remain
//! outside this module.
//!
//! ```
//! use sens::{Bit2, Bit3, BitPacker};
//!
//! let mut packer = BitPacker::new();
//! packer.push(Bit3::new(0b101).unwrap());
//! packer.push(Bit2::new(0b01).unwrap());
//! packer.push(Bit3::new(0b111).unwrap());
//!
//! let packed = packer.finish();
//! assert_eq!(packed.bytes(), &[0b1010_1111]);
//! assert_eq!(packed.bit_len(), 8);
//! ```

use crate::bits::Bits;
use crate::domain_ladder::DomainCoordinate;
use crate::Bit9;

/// Canonical dense payload bytes plus the exact count of meaningful bits.
///
/// Unused low bits in the final byte, when any, are always zero and are not
/// part of the payload. No padding exists between words.
#[derive(Clone, Eq, PartialEq)]
pub struct PackedBitstream {
    bytes: Vec<u8>,
    bit_len: usize,
}

impl PackedBitstream {
    /// Reconstruct a canonical packed payload from bytes and an exact bit count.
    ///
    /// The byte slice must be minimal for `bit_len`, and every unused low bit
    /// in the final byte must be zero. This rejects alternate padded spellings
    /// of the same payload.
    pub fn from_parts(bytes: Vec<u8>, bit_len: usize) -> Option<Self> {
        let required_bytes = byte_len_for_bits(bit_len);
        if bytes.len() != required_bytes {
            return None;
        }

        let capacity_bits = bytes.len().checked_mul(8)?;
        if bit_len > capacity_bits {
            return None;
        }

        let valid_last = bit_len % 8;
        if valid_last != 0 {
            let unused = 8 - valid_last;
            let unused_mask = ((1u16 << unused) - 1) as u8;
            if bytes.last().copied().unwrap_or(0) & unused_mask != 0 {
                return None;
            }
        }

        Some(Self { bytes, bit_len })
    }

    /// Minimal physical byte payload.
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }

    /// Exact number of meaningful bits in the payload.
    pub const fn bit_len(&self) -> usize {
        self.bit_len
    }

    /// Number of physical payload bytes.
    pub fn byte_len(&self) -> usize {
        self.bytes.len()
    }

    /// Number of meaningful bits in the final byte.
    ///
    /// Returns zero for an empty payload and eight for a non-empty payload that
    /// ends exactly on a byte boundary.
    pub const fn valid_bits_in_last_byte(&self) -> u8 {
        if self.bit_len == 0 {
            0
        } else {
            let remainder = self.bit_len % 8;
            if remainder == 0 {
                8
            } else {
                remainder as u8
            }
        }
    }

    /// Read an exact-width word at a known bit offset.
    ///
    /// Word boundaries are deliberately supplied by the caller: this payload
    /// format does not smuggle a second semantic grammar into the byte stream.
    pub fn read<const N: usize>(&self, bit_offset: usize) -> Option<Bits<N>> {
        if N == 0 || N > 8 {
            return None;
        }

        let end = bit_offset.checked_add(N)?;
        if end > self.bit_len {
            return None;
        }

        let byte_index = bit_offset / 8;
        let bit_in_byte = bit_offset % 8;
        let first = *self.bytes.get(byte_index)? as u16;
        let second = if bit_in_byte + N > 8 {
            *self.bytes.get(byte_index + 1)? as u16
        } else {
            0
        };

        // N <= 8, so every word fits in at most two adjacent bytes.
        // Align those bytes into one MSB-first 16-bit window, then extract
        // the requested exact-width field with one shift and mask.
        let window = (first << 8) | second;
        let shift = 16 - bit_in_byte - N;
        let mask = (1u16 << N) - 1;
        Bits::<N>::new(((window >> shift) & mask) as u8)
    }

    /// Extract up to ten exact semantic bits from at most three bytes.
    ///
    /// D10 at a seven-bit offset spans 17 physical bits. This is a fixed
    /// MSB-first window, not a decimal conversion or width inference.
    /// W1–W8 retain their dedicated existing fast path.
    fn read_bounded_window(&self, bit_offset: usize, width: usize) -> Option<u16> {
        if !(1..=10).contains(&width) {
            return None;
        }
        let end = bit_offset.checked_add(width)?;
        if end > self.bit_len {
            return None;
        }

        let byte_index = bit_offset / 8;
        let start_in_byte = bit_offset % 8;
        let occupied = start_in_byte + width;
        let first = u32::from(*self.bytes.get(byte_index)?);
        let second = if occupied > 8 {
            u32::from(*self.bytes.get(byte_index + 1)?)
        } else {
            0
        };
        let third = if occupied > 16 {
            u32::from(*self.bytes.get(byte_index + 2)?)
        } else {
            0
        };
        let window = (first << 16) | (second << 8) | third;
        let shift = 24 - occupied;
        let mask = (1u32 << width) - 1;
        Some(((window >> shift) & mask) as u16)
    }

    /// Read one exact W9 word at a known bit offset, without a per-bit scan.
    ///
    /// W9 stays distinct from the W1–W8 `Bits<N>` fast path.
    pub fn read_w9(&self, bit_offset: usize) -> Option<Bit9> {
        Bit9::new(self.read_bounded_window(bit_offset, 9)?)
    }

    /// Read a width-qualified D1–D10 coordinate without per-bit scanning.
    ///
    /// Width comes from the caller's grammar. No payload grants callability.
    pub fn read_coordinate(&self, bit_offset: usize, width: u8) -> Option<DomainCoordinate> {
        DomainCoordinate::new(width, self.read_bounded_window(bit_offset, usize::from(width))?)
    }

    /// Split the mechanical container into its physical payload and exact bit
    /// count. The returned byte vector alone is not a complete identity.
    pub fn into_parts(self) -> (Vec<u8>, usize) {
        (self.bytes, self.bit_len)
    }
}

/// Sequential dense packer for `Bits<1>..Bits<8>`.
///
/// Every pushed word is appended immediately after the preceding word. Bytes
/// are emitted only because physical storage is byte-addressed; they never
/// align or pad semantic words.
#[derive(Default)]
pub struct BitPacker {
    bytes: Vec<u8>,
    bit_len: usize,
}

impl BitPacker {
    pub const fn new() -> Self {
        Self {
            bytes: Vec::new(),
            bit_len: 0,
        }
    }

    /// Reserve enough storage for approximately `bit_capacity` payload bits.
    pub fn with_capacity_bits(bit_capacity: usize) -> Self {
        Self {
            bytes: Vec::with_capacity(byte_len_for_bits(bit_capacity)),
            bit_len: 0,
        }
    }

    /// Current exact payload length.
    pub const fn bit_len(&self) -> usize {
        self.bit_len
    }

    /// Current minimal physical byte count.
    pub fn byte_len(&self) -> usize {
        self.bytes.len()
    }

    /// Append one exact-width word and return its starting bit offset.
    ///
    /// Bits are copied most-significant first, matching `Bits<N>::bit`.
    /// No alignment or padding is inserted before or after the word.
    pub fn push<const N: usize>(&mut self, word: Bits<N>) -> usize {
        // Bits<N> is constructible only for 1..=8. The same bounded
        // MSB-first window serves all exact widths without a per-bit loop.
        self.append_exact_window(N, u16::from(word.packed_bits()))
    }

    /// Append one exact small-domain word through a three-byte MSB window.
    ///
    /// The input width and payload were validated by Bit9/DomainCoordinate.
    /// Existing low tail bits are zero; no padding occurs between words.
    /// At most three target bytes are touched, even for unaligned D10.
    #[inline]
    fn append_exact_window(&mut self, width: usize, bits: u16) -> usize {
        debug_assert!((1..=10).contains(&width));
        debug_assert!(u32::from(bits) < (1u32 << width));
        let start = self.bit_len;
        let end = start.checked_add(width).expect("packed bit count overflow");
        let byte_index = start / 8;
        let occupied = start % 8 + width;
        let window = u32::from(bits) << (24 - occupied);

        self.bytes.resize(byte_len_for_bits(end), 0);
        self.bytes[byte_index] |= (window >> 16) as u8;
        if occupied > 8 {
            self.bytes[byte_index + 1] |= (window >> 8) as u8;
        }
        if occupied > 16 {
            self.bytes[byte_index + 2] |= window as u8;
        }
        self.bit_len = end;
        start
    }

    /// Append one exact W9 word with no interior alignment or padding.
    pub fn push_w9(&mut self, word: Bit9) -> usize {
        self.append_exact_window(9, word.packed_bits())
    }

    /// Append a ratified D1–D10 coordinate, retaining exact width and zeros.
    ///
    /// This mechanism never infers domain identity from the numeric payload.
    pub fn push_coordinate(&mut self, coordinate: DomainCoordinate) -> usize {
        self.append_exact_window(usize::from(coordinate.width()), coordinate.bits())
    }

    /// Finish packing without adding any semantic padding or delimiter.
    pub fn finish(self) -> PackedBitstream {
        PackedBitstream {
            bytes: self.bytes,
            bit_len: self.bit_len,
        }
    }
}

const fn byte_len_for_bits(bit_len: usize) -> usize {
    (bit_len / 8) + if bit_len.is_multiple_of(8) { 0 } else { 1 }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bits::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8};

    fn reference_read<const N: usize>(
        packed: &PackedBitstream,
        bit_offset: usize,
    ) -> Option<Bits<N>> {
        if N == 0 || N > 8 {
            return None;
        }
        let end = bit_offset.checked_add(N)?;
        if end > packed.bit_len {
            return None;
        }

        let mut value = 0u8;
        for position in bit_offset..end {
            let byte = packed.bytes[position / 8];
            let bit_in_byte = position % 8;
            let bit = (byte >> (7 - bit_in_byte)) & 1;
            value = (value << 1) | bit;
        }
        Bits::<N>::new(value)
    }

    fn assert_read_parity<const N: usize>(packed: &PackedBitstream) {
        for offset in 0..=packed.bit_len {
            assert_eq!(
                packed.read::<N>(offset).map(|word| word.packed_bits()),
                reference_read::<N>(packed, offset).map(|word| word.packed_bits()),
                "N={N} offset={offset} bit_len={}",
                packed.bit_len
            );
        }
    }

    #[test]
    fn two_byte_window_matches_reference_for_all_patterns_and_widths() {
        for raw in 0u32..=u16::MAX as u32 {
            let packed = PackedBitstream {
                bytes: vec![(raw >> 8) as u8, raw as u8],
                bit_len: 16,
            };

            assert_read_parity::<1>(&packed);
            assert_read_parity::<2>(&packed);
            assert_read_parity::<3>(&packed);
            assert_read_parity::<4>(&packed);
            assert_read_parity::<5>(&packed);
            assert_read_parity::<6>(&packed);
            assert_read_parity::<7>(&packed);
            assert_read_parity::<8>(&packed);
        }
    }

    #[test]
    fn two_byte_window_matches_reference_on_partial_tails() {
        for raw in [0x0000u16, 0xffff, 0xa55a, 0x5aa5] {
            for bit_len in 1usize..16 {
                let byte_len = byte_len_for_bits(bit_len);
                let mut bytes = vec![(raw >> 8) as u8, raw as u8];
                bytes.truncate(byte_len);

                let remainder = bit_len % 8;
                if remainder != 0 {
                    let unused = 8 - remainder;
                    let keep_mask = !(((1u16 << unused) - 1) as u8);
                    *bytes.last_mut().unwrap() &= keep_mask;
                }

                let packed = PackedBitstream::from_parts(bytes, bit_len).unwrap();
                assert_read_parity::<1>(&packed);
                assert_read_parity::<2>(&packed);
                assert_read_parity::<3>(&packed);
                assert_read_parity::<4>(&packed);
                assert_read_parity::<5>(&packed);
                assert_read_parity::<6>(&packed);
                assert_read_parity::<7>(&packed);
                assert_read_parity::<8>(&packed);
                assert!(packed.read::<0>(0).is_none());
                assert!(packed.read::<9>(0).is_none());
            }
        }
    }

    #[test]
    fn program_words_fill_bytes_sequentially() {
        let mut packer = BitPacker::new();

        let offsets = [
            packer.push(Bit3::new(0b101).unwrap()),
            packer.push(Bit2::new(0b01).unwrap()),
            packer.push(Bit3::new(0b111).unwrap()),
            packer.push(Bit1::new(0b0).unwrap()),
            packer.push(Bit4::new(0b1100).unwrap()),
            packer.push(Bit3::new(0b001).unwrap()),
        ];

        let packed = packer.finish();

        assert_eq!(offsets, [0, 3, 5, 8, 9, 13]);
        assert_eq!(packed.bit_len(), 16);
        assert_eq!(packed.bytes(), &[0b1010_1111, 0b0110_0001]);
        assert_eq!(packed.byte_len(), 2);

        assert_eq!(packed.read::<3>(offsets[0]).unwrap().packed_bits(), 0b101);
        assert_eq!(packed.read::<2>(offsets[1]).unwrap().packed_bits(), 0b01);
        assert_eq!(packed.read::<3>(offsets[2]).unwrap().packed_bits(), 0b111);
        assert_eq!(packed.read::<1>(offsets[3]).unwrap().packed_bits(), 0b0);
        assert_eq!(packed.read::<4>(offsets[4]).unwrap().packed_bits(), 0b1100);
        assert_eq!(packed.read::<3>(offsets[5]).unwrap().packed_bits(), 0b001);
    }

    #[test]
    fn one_word_can_cross_a_physical_byte_boundary() {
        let mut packer = BitPacker::new();
        let first = packer.push(Bit7::new(0b1010101).unwrap());
        let crossing = packer.push(Bit3::new(0b110).unwrap());
        let packed = packer.finish();

        assert_eq!(first, 0);
        assert_eq!(crossing, 7);
        assert_eq!(packed.bit_len(), 10);
        assert_eq!(packed.bytes(), &[0b1010_1011, 0b1000_0000]);
        assert_eq!(packed.valid_bits_in_last_byte(), 2);
        assert_eq!(packed.read::<7>(first).unwrap().packed_bits(), 0b1010101);
        assert_eq!(packed.read::<3>(crossing).unwrap().packed_bits(), 0b110);
    }

    #[test]
    fn structural_bit_patterns_are_payload_not_delimiters() {
        let mut packer = BitPacker::new();
        let offsets = [
            packer.push(Bit2::new(0b00).unwrap()),
            packer.push(Bit2::new(0b01).unwrap()),
            packer.push(Bit2::new(0b10).unwrap()),
            packer.push(Bit2::new(0b11).unwrap()),
        ];
        let packed = packer.finish();

        assert_eq!(packed.bytes(), &[0b0001_1011]);
        for (offset, expected) in offsets.into_iter().zip([0b00, 0b01, 0b10, 0b11]) {
            assert_eq!(packed.read::<2>(offset).unwrap().packed_bits(), expected);
        }
    }

    fn assert_exact_block<const N: usize>(count: usize, raw: u8) {
        let word = Bits::<N>::new(raw).unwrap();
        let mut packer = BitPacker::new();

        for _ in 0..count {
            packer.push(word);
        }

        let packed = packer.finish();
        assert_eq!(packed.bit_len(), count * N);
        assert_eq!(packed.byte_len(), (count * N) / 8);
        assert_eq!(packed.valid_bits_in_last_byte(), 8);
    }

    #[test]
    fn natural_homogeneous_blocks_have_zero_wasted_bits() {
        assert_exact_block::<1>(8, 1);
        assert_exact_block::<2>(4, 0b10);
        assert_exact_block::<3>(8, 0b101);
        assert_exact_block::<4>(2, 0b1010);
        assert_exact_block::<5>(8, 0b10101);
        assert_exact_block::<6>(4, 0b101010);
        assert_exact_block::<7>(8, 0b1010101);
        assert_exact_block::<8>(1, 0b10101010);
    }

    #[derive(Clone, Copy)]
    enum SmallWord {
        W1(Bit1),
        W2(Bit2),
        W3(Bit3),
    }

    impl SmallWord {
        fn width(self) -> usize {
            match self {
                Self::W1(_) => 1,
                Self::W2(_) => 2,
                Self::W3(_) => 3,
            }
        }

        fn raw(self) -> u8 {
            match self {
                Self::W1(word) => word.packed_bits(),
                Self::W2(word) => word.packed_bits(),
                Self::W3(word) => word.packed_bits(),
            }
        }

        fn push(self, packer: &mut BitPacker) -> usize {
            match self {
                Self::W1(word) => packer.push(word),
                Self::W2(word) => packer.push(word),
                Self::W3(word) => packer.push(word),
            }
        }

        fn read(self, packed: &PackedBitstream, offset: usize) -> u8 {
            match self {
                Self::W1(_) => packed.read::<1>(offset).unwrap().packed_bits(),
                Self::W2(_) => packed.read::<2>(offset).unwrap().packed_bits(),
                Self::W3(_) => packed.read::<3>(offset).unwrap().packed_bits(),
            }
        }
    }

    fn small_words() -> Vec<SmallWord> {
        let mut words = Vec::new();
        for raw in 0..2 {
            words.push(SmallWord::W1(Bit1::new(raw).unwrap()));
        }
        for raw in 0..4 {
            words.push(SmallWord::W2(Bit2::new(raw).unwrap()));
        }
        for raw in 0..8 {
            words.push(SmallWord::W3(Bit3::new(raw).unwrap()));
        }
        words
    }

    #[test]
    fn all_bounded_three_word_programs_over_widths_one_to_three_hit_the_lower_bound() {
        let words = small_words();

        for &a in &words {
            for &b in &words {
                for &c in &words {
                    let program = [a, b, c];
                    let mut packer = BitPacker::new();
                    let mut offsets = [0usize; 3];

                    for (slot, word) in program.into_iter().enumerate() {
                        offsets[slot] = word.push(&mut packer);
                    }

                    let packed = packer.finish();
                    let payload_bits: usize = program.into_iter().map(SmallWord::width).sum();
                    let minimum_bytes = byte_len_for_bits(payload_bits);

                    assert_eq!(packed.bit_len(), payload_bits);
                    assert_eq!(packed.byte_len(), minimum_bytes);

                    for (index, word) in program.into_iter().enumerate() {
                        assert_eq!(word.read(&packed, offsets[index]), word.raw());
                    }
                }
            }
        }
    }

    #[test]
    fn canonical_parts_reject_extra_bytes_and_nonzero_tail_padding() {
        assert!(PackedBitstream::from_parts(vec![], 0).is_some());
        assert!(PackedBitstream::from_parts(vec![0], 0).is_none());
        assert!(PackedBitstream::from_parts(vec![0b1010_0000], 3).is_some());
        assert!(PackedBitstream::from_parts(vec![0b1010_0001], 3).is_none());
        assert!(PackedBitstream::from_parts(vec![0b1010_0000, 0], 3).is_none());
        assert!(PackedBitstream::from_parts(vec![0b1010_0000], 9).is_none());
    }

    #[test]
    fn w9_crosses_byte_boundary_without_interior_padding() {
        let mut packer = BitPacker::new();
        let first = packer.push(Bit7::new(0b1010101).unwrap());
        let w9 = packer.push_w9(Bit9::new(0b1_00000001).unwrap());
        let packed = packer.finish();

        assert_eq!(first, 0);
        assert_eq!(w9, 7);
        assert_eq!(packed.bit_len(), 16);
        assert_eq!(packed.byte_len(), 2);
        assert_eq!(packed.read::<7>(first).unwrap().packed_bits(), 0b1010101);
        assert_eq!(packed.read_w9(w9).unwrap().packed_bits(), 0b1_00000001);
    }

    #[test]
    fn final_tail_is_the_only_unused_payload_space() {
        let mut packer = BitPacker::with_capacity_bits(13);
        packer.push(Bit1::new(1).unwrap());
        packer.push(Bit2::new(0b01).unwrap());
        packer.push(Bit3::new(0b101).unwrap());
        packer.push(Bit3::new(0b011).unwrap());
        packer.push(Bit4::new(0b1100).unwrap());

        let packed = packer.finish();

        assert_eq!(packed.bit_len(), 13);
        assert_eq!(packed.byte_len(), 2);
        assert_eq!(packed.valid_bits_in_last_byte(), 5);
        assert_eq!(packed.bytes()[1] & 0b0000_0111, 0);
        assert!(packed.read::<1>(13).is_none());
    }

    #[test]
    fn every_width_one_to_eight_can_cross_and_round_trip() {
        let mut packer = BitPacker::new();
        let offsets = [
            packer.push(Bit1::new(1).unwrap()),
            packer.push(Bit2::new(0b10).unwrap()),
            packer.push(Bit3::new(0b101).unwrap()),
            packer.push(Bit4::new(0b1010).unwrap()),
            packer.push(Bit5::new(0b10101).unwrap()),
            packer.push(Bit6::new(0b101010).unwrap()),
            packer.push(Bit7::new(0b1010101).unwrap()),
            packer.push(Bit8::new(0b10101010).unwrap()),
        ];
        let packed = packer.finish();

        assert_eq!(packed.bit_len(), 36);
        assert_eq!(packed.byte_len(), 5);
        assert_eq!(packed.read::<1>(offsets[0]).unwrap().packed_bits(), 1);
        assert_eq!(packed.read::<2>(offsets[1]).unwrap().packed_bits(), 0b10);
        assert_eq!(packed.read::<3>(offsets[2]).unwrap().packed_bits(), 0b101);
        assert_eq!(packed.read::<4>(offsets[3]).unwrap().packed_bits(), 0b1010);
        assert_eq!(packed.read::<5>(offsets[4]).unwrap().packed_bits(), 0b10101);
        assert_eq!(packed.read::<6>(offsets[5]).unwrap().packed_bits(), 0b101010);
        assert_eq!(packed.read::<7>(offsets[6]).unwrap().packed_bits(), 0b1010101);
        assert_eq!(packed.read::<8>(offsets[7]).unwrap().packed_bits(), 0b10101010);
    }
 
    #[test]
    fn exact_d1_through_d10_are_dense_with_only_one_final_tail() {
        let coordinates: Vec<_> = [
            (1u8, 1u16), (2, 2), (3, 5), (4, 10), (5, 21),
            (6, 42), (7, 85), (8, 170), (9, 257), (10, 1023),
        ]
        .into_iter()
        .map(|(width, bits)| DomainCoordinate::new(width, bits).unwrap())
        .collect();
        let mut packer = BitPacker::new();
        let mut offsets = Vec::new();
        for coordinate in &coordinates {
            offsets.push(packer.push_coordinate(*coordinate));
        }
        let packed = packer.finish();
        assert_eq!(packed.bit_len(), 55, "1+2+...+10 must be 55 semantic bits");
        assert_eq!(packed.byte_len(), 7, "only seven physical bytes, not ten words");
        assert_eq!(packed.valid_bits_in_last_byte(), 7);
        assert_eq!(packed.bytes()[6] & 1, 0, "only final container slack may be zeroed");
        for (coordinate, offset) in coordinates.iter().zip(offsets) {
            assert_eq!(
                packed.read_coordinate(offset, coordinate.width()),
                Some(*coordinate),
                "word width and bits survive crossing physical byte boundaries"
            );
        }
        assert_ne!(
            DomainCoordinate::new(9, 257),
            DomainCoordinate::new(10, 257),
            "equal numeric payloads never establish equal domain identity"
        );
    }

    #[test]
    fn all_domain_writes_match_independent_bitwise_reference() {
        for width in 1u8..=10 {
            for bits in 0u16..(1u16 << width) {
                let coordinate = DomainCoordinate::new(width, bits).unwrap();
                for prefix in 0..8usize {
                    let mut packer = BitPacker::new();
                    for _ in 0..prefix {
                        packer.push(Bit1::new(1).unwrap());
                    }
                    assert_eq!(packer.push_coordinate(coordinate), prefix);
                    let packed = packer.finish();

                    // Independent one-bit-at-a-time reference: no reuse of
                    // append_exact_window, read_coordinate or packed words.
                    let mut expected = vec![0u8; (prefix + usize::from(width) + 7) / 8];
                    for position in 0..prefix {
                        expected[position / 8] |= 1 << (7 - position % 8);
                    }
                    for bit_index in 0..usize::from(width) {
                        let bit = (bits >> (usize::from(width) - 1 - bit_index)) & 1;
                        if bit != 0 {
                            let position = prefix + bit_index;
                            expected[position / 8] |= 1 << (7 - position % 8);
                        }
                    }
                    assert_eq!(packed.bytes(), expected.as_slice(),
                        "D{width} payload={bits:b} offset={prefix}");
                    assert_eq!(packed.bit_len(), prefix + usize::from(width));
                    assert_eq!(packed.read_coordinate(prefix, width), Some(coordinate));
                }
            }
        }
    }

    #[test]
    fn all_d1_d10_payloads_round_trip_at_every_byte_alignment() {
        for width in 1u8..=10 {
            for bits in 0u16..(1u16 << width) {
                let coordinate = DomainCoordinate::new(width, bits).unwrap();
                for prefix in 0..8usize {
                    let mut packer = BitPacker::new();
                    for _ in 0..prefix {
                        packer.push(crate::Bit1::new(1).unwrap());
                    }
                    let offset = packer.push_coordinate(coordinate);
                    assert_eq!(offset, prefix);
                    let packed = packer.finish();
                    assert_eq!(packed.bit_len(), prefix + usize::from(width));
                    assert_eq!(packed.byte_len(), (packed.bit_len() + 7) / 8);
                    assert_eq!(packed.read_coordinate(offset, width), Some(coordinate));
                    assert_eq!(packed.read_coordinate(offset + 1, width), None);
                    if width == 9 {
                        assert_eq!(packed.read_w9(offset).unwrap().packed_bits(), bits);
                        assert!(packed.read_w9(offset + 1).is_none());
                    }
                }
            }
        }
    }

    #[test]
    fn three_byte_window_preserves_d10_and_reports_every_bit_of_cost() {
        // 7 + 10 + 3 = 20 біт, рівно три байти і лише 4 кінцеві
        // невикористані біти. Жодного вирівнювання між координатами.
        let d10 = DomainCoordinate::new(10, 0b10_1010_0101).unwrap();
        let d3 = DomainCoordinate::new(3, 0b111).unwrap();
        let mut packer = BitPacker::new();
        let prefix = packer.push(crate::Bit7::new(0b1010101).unwrap());
        let middle = packer.push_coordinate(d10);
        let suffix = packer.push_coordinate(d3);
        let packed = packer.finish();

        assert_eq!((prefix, middle, suffix), (0, 7, 17));
        assert_eq!(packed.bit_len(), 20, "семантичні біти: 7+10+3");
        assert_eq!(packed.byte_len(), 3, "не три байти на слово");
        assert_eq!(packed.valid_bits_in_last_byte(), 4);
        assert_eq!(packed.read_coordinate(middle, 10), Some(d10));
        assert_eq!(packed.read_coordinate(suffix, 3), Some(d3));
        assert_eq!(packed.read_coordinate(middle, 9).unwrap().width(), 9,
                   "ширину задає граматика, не випадковий payload");

        // Пошкодження сусіднього D3 змінює лише D3, а не десять бітів D10.
        let (bytes, bit_len) = packed.into_parts();
        let mut neighbor_changed = bytes.clone();
        neighbor_changed[2] ^= 0b0100_0000;
        let neighbor = PackedBitstream::from_parts(neighbor_changed, bit_len).unwrap();
        assert_eq!(neighbor.read_coordinate(middle, 10), Some(d10));
        assert_ne!(neighbor.read_coordinate(suffix, 3), Some(d3));

        // Невикористаний четвертий молодший біт не стає ще одним словом.
        let mut bad_padding = bytes;
        bad_padding[2] |= 1;
        assert!(PackedBitstream::from_parts(bad_padding, bit_len).is_none());
        assert!(neighbor.read_coordinate(middle + 1, 10).is_some(),
                "читач голих бітів не знає меж: лише явний розклад ширин");
        assert!(neighbor.read_coordinate(suffix + 1, 3).is_none(),
                "за межами двадцяти змістових бітів читання заборонене");
    }

    #[test]
    fn domain_coordinate_reader_fails_closed_on_bad_width_and_noncanonical_padding() {
        let mut packer = BitPacker::new();
        let start = packer.push_coordinate(DomainCoordinate::new(10, 0b10_1010_0101).unwrap());
        let packed = packer.finish();
        assert_eq!(start, 0);
        assert_eq!(packed.bit_len(), 10);
        assert_eq!(packed.bytes(), &[0b1010_1001, 0b0100_0000]);
        assert!(packed.read_coordinate(0, 0).is_none());
        assert!(packed.read_coordinate(0, 11).is_none());
        assert!(packed.read_coordinate(1, 10).is_none());
        assert_eq!(
            packed.read_coordinate(0, 10).unwrap().bits(),
            0b10_1010_0101
        );
        let (bytes, bit_len) = packed.into_parts();
        assert!(PackedBitstream::from_parts(bytes.clone(), bit_len).is_some());
        let mut corrupted = bytes;
        *corrupted.last_mut().unwrap() |= 1;
        assert!(PackedBitstream::from_parts(corrupted, bit_len).is_none());
    }
}
