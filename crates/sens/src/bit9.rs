//! Exact nine-bit mechanical carrier for the W9 runtime boundary.
//!
//! This is deliberately separate from `Bits<1..=8>`: the small-word carrier
//! remains one host byte and byte-for-byte unchanged. `Bit9` uses `u16`
//! because a nine-bit payload must never be truncated, masked, or routed
//! through historical SID8/Function8 storage.

/// Exact W9 payload, mechanically bounded to 0..=511.
#[repr(transparent)]
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct Bit9(u16);

impl Bit9 {
    pub const WIDTH: usize = 9;
    pub const MAX: u16 = 0x01ff;

    /// Construct only an exact nine-bit payload.
    pub const fn new(value: u16) -> Option<Self> {
        if value <= Self::MAX {
            Some(Self(value))
        } else {
            None
        }
    }

    pub const fn width() -> usize {
        Self::WIDTH
    }

    pub const fn packed_bits(self) -> u16 {
        self.0
    }

    pub const fn bit(self, index: usize) -> Option<bool> {
        if index >= Self::WIDTH {
            return None;
        }
        let shift = Self::WIDTH - 1 - index;
        Some(((self.0 >> shift) & 1) != 0)
    }
}

