//! Exact nine-bit mechanical carrier for the W9 runtime boundary.
//!
//! This is deliberately separate from `Bits<1..=8>`: the small-word carrier
//! remains one host byte and byte-for-byte unchanged. `Bit9` uses `u16`
//! because a nine-bit payload must never be truncated, masked, or routed
//! through historical SID8/Function8 storage.

/// Exact W9 payload, mechanically bounded to 0..=511.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn admits_exactly_the_nine_bit_range_without_byte_truncation() {
        assert_eq!(Bit9::new(0).unwrap().packed_bits(), 0);
        assert_eq!(Bit9::new(0x00ff).unwrap().packed_bits(), 0x00ff);
        assert_eq!(Bit9::new(0x0100).unwrap().packed_bits(), 0x0100);
        assert_eq!(Bit9::new(0x01ff).unwrap().packed_bits(), 0x01ff);
        assert!(Bit9::new(0x0200).is_none());
    }

    #[test]
    fn high_ninth_bit_is_observable_and_not_an_alias_of_low_byte() {
        let low = Bit9::new(0x0001).unwrap();
        let high = Bit9::new(0x0101).unwrap();
        assert_ne!(low, high);
        assert_eq!(low.bit(0), Some(false));
        assert_eq!(high.bit(0), Some(true));
        assert_eq!(high.bit(8), Some(true));
    }
}
