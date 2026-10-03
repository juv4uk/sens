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
        let start = self.bit_len;

        for index in 0..N {
            let bit_in_byte = self.bit_len % 8;
            if bit_in_byte == 0 {
                self.bytes.push(0);
            }

            if word.bit(index) == Some(true) {
                let byte_index = self.bit_len / 8;
                self.bytes[byte_index] |= 1 << (7 - bit_in_byte);
            }

            self.bit_len += 1;
        }

        start
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
}
