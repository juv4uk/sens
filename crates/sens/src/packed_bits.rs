//! ZIG-OWNED: physical bit-packing is implemented by the sterile Zig ABI on
//! native and wasm32 targets. Rust BitPacker only stages exact-width value records,
//! then delegates raw MSB-first byte emission to sens_zig_bitpack_fields.
//! PackedBitstream remains the exact-byte-count container/read adapter.
//!
//! This module assigns no SENS meaning and invents no word boundaries. The
//! caller owns exact widths and the meaningful bit count; Rust contains no
//! physical bit-emission path.
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
#[derive(Clone, Debug, Eq, PartialEq)]
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
    /// Small-width values retain their compact dedicated fast path.
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

    /// Read one exact nine-bit compatibility value at a known bit offset,
    /// without a per-bit scan. This is an implementation path, not a domain rung.
    pub fn read_w9(&self, bit_offset: usize) -> Option<Bit9> {
        Bit9::new(self.read_bounded_window(bit_offset, 9)?)
    }

    /// Read a width-qualified D1–D10 coordinate without per-bit scanning.
    ///
    /// Width comes from the caller's grammar. No payload grants callability.
    pub fn read_coordinate(&self, bit_offset: usize, width: u8) -> Option<DomainCoordinate> {
        DomainCoordinate::new(
            width,
            self.read_bounded_window(bit_offset, usize::from(width))?,
        )
    }

    /// Read a bounded MSB-first chunk without interpreting its semantic role.
    ///
    /// This is a private transport helper for stream concatenation. The caller
    /// supplies the exact chunk width; the byte payload never determines it.
    fn read_chunk(&self, bit_offset: usize, width: usize) -> Option<u8> {
        if width == 0 || width > 8 {
            return None;
        }
        let end = bit_offset.checked_add(width)?;
        if end > self.bit_len {
            return None;
        }

        let byte_index = bit_offset / 8;
        let bit_in_byte = bit_offset % 8;
        let first = u16::from(*self.bytes.get(byte_index)?);
        let second = if bit_in_byte + width > 8 {
            u16::from(*self.bytes.get(byte_index + 1)?)
        } else {
            0
        };
        let window = (first << 8) | second;
        let shift = 16 - bit_in_byte - width;
        let mask = (1u16 << width) - 1;
        Some(((window >> shift) & mask) as u8)
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
/// Logical stream builder. Native builds delegate physical packing to Zig's
/// single exact-width MSB-first ABI; wasm32 temporarily retains the named
/// reference path until the Zig archive is built for that final linker profile.
/// Width-qualified record builder. Rust never emits physical packed bytes;
/// the canonical Zig ABI is the sole packer for native and wasm32 targets.
#[derive(Default)]
pub struct BitPacker {
    records: Vec<u8>,
    bit_len: usize,
}

#[link(name = "sens_zig_transport", kind = "static")]
unsafe extern "C" {
    /// Input records: repeated [width:u8][value:u64 big-endian]. Output is the
    /// canonical raw MSB-first payload. capacity=0 queries the exact byte count.
    fn sens_zig_bitpack_fields(
        src: *const u8,
        byte_len: usize,
        dst: *mut u8,
        capacity: usize,
    ) -> isize;
}

impl BitPacker {
    pub const fn new() -> Self {
        Self {
            records: Vec::new(),
            bit_len: 0,
        }
    }

    /// Reserve an estimate for a stream of this many meaningful bits.
    pub fn with_capacity_bits(bit_capacity: usize) -> Self {
        let record_capacity = byte_len_for_bits(bit_capacity).saturating_mul(9);
        Self {
            records: Vec::with_capacity(record_capacity),
            bit_len: 0,
        }
    }

    /// Current exact payload length.
    pub const fn bit_len(&self) -> usize {
        self.bit_len
    }

    /// Minimal byte count the final canonical payload will occupy.
    pub fn byte_len(&self) -> usize {
        byte_len_for_bits(self.bit_len)
    }

    /// Append one exact-width word and return its starting bit offset.
    pub fn push<const N: usize>(&mut self, word: Bits<N>) -> usize {
        self.append_exact_window(N, u16::from(word.packed_bits()))
    }

    /// Append one exact W9 word without truncating the ninth bit.
    pub fn push_w9(&mut self, word: Bit9) -> usize {
        self.append_exact_window(9, word.packed_bits())
    }

    /// Append a ratified D1-D10 coordinate without inferring identity from value.
    pub fn push_coordinate(&mut self, coordinate: DomainCoordinate) -> usize {
        self.append_exact_window(usize::from(coordinate.width()), coordinate.bits())
    }

    /// Stage width and value only. Physical MSB-first emission is owned by Zig.
    #[inline]
    fn append_exact_window(&mut self, width: usize, bits: u16) -> usize {
        assert!((1..=10).contains(&width), "unsupported exact-width carrier");
        assert!(
            u32::from(bits) < (1u32 << width),
            "payload exceeds exact width"
        );
        let start = self.bit_len;
        let end = start.checked_add(width).expect("packed bit count overflow");
        self.records
            .try_reserve(9)
            .expect("reserve Zig field record");
        self.records.push(width as u8);
        self.records
            .extend_from_slice(&u64::from(bits).to_be_bytes());
        self.bit_len = end;
        start
    }

    /// Append a canonical stream by staging its declared bit chunks as fields.
    pub fn push_stream(&mut self, source: &PackedBitstream) -> Option<usize> {
        let start = self.bit_len;
        let end = start.checked_add(source.bit_len)?;
        let chunks = source.bit_len.checked_add(7)? / 8;
        self.records.try_reserve(chunks.checked_mul(9)?).ok()?;

        let mut source_offset = 0usize;
        while source_offset < source.bit_len {
            let width = (source.bit_len - source_offset).min(8);
            let chunk = source.read_chunk(source_offset, width)?;
            self.append_exact_window(width, u16::from(chunk));
            source_offset += width;
        }
        debug_assert_eq!(self.bit_len, end);
        Some(start)
    }

    /// Finish packing through the canonical Zig ABI.
    pub fn finish(self) -> PackedBitstream {
        self.try_finish()
            .unwrap_or_else(|error| panic!("Zig bitpack failed: {error}"))
    }

    pub fn try_finish(self) -> Result<PackedBitstream, String> {
        if self.bit_len == 0 {
            if !self.records.is_empty() {
                return Err("empty Zig bitstream has non-empty field records".into());
            }
            return Ok(PackedBitstream {
                bytes: Vec::new(),
                bit_len: 0,
            });
        }
        let queried = unsafe {
            sens_zig_bitpack_fields(
                self.records.as_ptr(),
                self.records.len(),
                std::ptr::NonNull::<u8>::dangling().as_ptr(),
                0,
            )
        };
        let required = usize::try_from(queried)
            .ok()
            .filter(|&size| size == byte_len_for_bits(self.bit_len))
            .ok_or_else(|| format!("Zig bitpack size query rejected: {queried}"))?;
        let mut bytes = vec![0u8; required];
        let written = unsafe {
            sens_zig_bitpack_fields(
                self.records.as_ptr(),
                self.records.len(),
                bytes.as_mut_ptr(),
                bytes.len(),
            )
        };
        if written != queried {
            return Err(format!(
                "Zig bitpack output mismatch: expected={queried} actual={written}"
            ));
        }
        PackedBitstream::from_parts(bytes, self.bit_len)
            .ok_or_else(|| "Zig returned non-canonical packed tail".into())
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
        assert_eq!(
            packed.read::<6>(offsets[5]).unwrap().packed_bits(),
            0b101010
        );
        assert_eq!(
            packed.read::<7>(offsets[6]).unwrap().packed_bits(),
            0b1010101
        );
        assert_eq!(
            packed.read::<8>(offsets[7]).unwrap().packed_bits(),
            0b10101010
        );
    }

    #[test]
    fn exact_d1_through_d10_are_dense_with_only_one_final_tail() {
        let coordinates: Vec<_> = [
            (1u8, 1u16),
            (2, 2),
            (3, 5),
            (4, 10),
            (5, 21),
            (6, 42),
            (7, 85),
            (8, 170),
            (9, 257),
            (10, 1023),
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
        assert_eq!(
            packed.byte_len(),
            7,
            "only seven physical bytes, not ten words"
        );
        assert_eq!(packed.valid_bits_in_last_byte(), 7);
        assert_eq!(
            packed.bytes()[6] & 1,
            0,
            "only final container slack may be zeroed"
        );
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
                    assert_eq!(
                        packed.bytes(),
                        expected.as_slice(),
                        "D{width} payload={bits:b} offset={prefix}"
                    );
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
    fn stream_concatenation_preserves_all_domain_bits_at_every_byte_offset() {
        // Include every D1-D10 coordinate, including all 1024 D10 payloads.
        // The width schedule stays here as grammar/test data, not in the stream.
        let mut source_packer = BitPacker::new();
        for width in 1u8..=10 {
            for bits in 0u16..(1u16 << width) {
                source_packer.push_coordinate(
                    DomainCoordinate::new(width, bits).expect("coordinate fits its width"),
                );
            }
        }
        let source = source_packer.finish();

        for prefix in 0..8usize {
            let mut destination = BitPacker::new();
            for index in 0..prefix {
                destination.push(crate::Bit1::new((index % 2) as u8).unwrap());
            }

            let start = destination
                .push_stream(&source)
                .expect("the finite bitstream length must fit");
            assert_eq!(start, prefix);
            let joined = destination.finish();
            assert_eq!(joined.bit_len(), prefix + source.bit_len());
            assert_eq!(joined.byte_len(), (joined.bit_len() + 7) / 8);
            assert!(
                PackedBitstream::from_parts(joined.bytes().to_vec(), joined.bit_len()).is_some(),
                "joined tail must be canonical"
            );

            for index in 0..source.bit_len() {
                assert!(
                    joined.read::<1>(start + index) == source.read::<1>(index),
                    "bit {index} changed when concatenated after prefix length {prefix}",
                );
            }
        }
    }

    #[test]
    fn stream_concatenation_handles_empty_aligned_and_partial_tail_inputs() {
        let empty = PackedBitstream::from_parts(Vec::new(), 0).unwrap();
        let aligned = PackedBitstream::from_parts(vec![0b1010_1100, 0b0111_0001], 16).unwrap();
        let partial = PackedBitstream::from_parts(vec![0b1010_1000], 5).unwrap();

        let mut packer = BitPacker::new();
        assert_eq!(packer.push_stream(&empty), Some(0));
        assert_eq!(packer.push_stream(&aligned), Some(0));
        assert_eq!(packer.push_stream(&partial), Some(16));

        let joined = packer.finish();
        assert_eq!(joined.bit_len(), 21);
        assert_eq!(joined.read::<8>(0).unwrap().packed_bits(), 0b1010_1100);
        assert_eq!(joined.read::<8>(8).unwrap().packed_bits(), 0b0111_0001);
        assert_eq!(joined.read::<5>(16).unwrap().packed_bits(), 0b10101);
        assert!(joined.read::<1>(21).is_none());
        assert!(PackedBitstream::from_parts(joined.bytes().to_vec(), joined.bit_len()).is_some());
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
