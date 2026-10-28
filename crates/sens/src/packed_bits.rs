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

