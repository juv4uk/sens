//! Exact eight-bit function sense (СЕНС).
//!
//! #1344 / #1386: Renames the technical acronym `SID` to the ontological term `sens` (СЕНС).
//! In `sens` / `sens`, exactly 256 functions exist in the `00000000..11111111` space.
//! Each eight-bit value is the direct `sens` (meaning, sense, вектор, сутність)
//! of the function itself, not an arbitrary database identifier.

use std::fmt;

/// Exact eight-bit function sense (СЕНС).
///
/// The function identity is exactly the eight bits themselves (`00000000..11111111`).
/// The packed byte is a private runtime/transport mechanism and is never the
/// alternate identity of the sens.
///
/// Deliberately NOT `Ord`/`PartialOrd` (wsm-lazarus owner, 2026-09-23:
/// "треба заборонити математичні операції над нашим сідом" -- mathematical
/// operations on our sens must be forbidden).
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Sens8(pub(crate) u8);

pub type Sens = Sens8;

impl Sens8 {
    /// Macro-only bridge from exactly eight source 0/1 characters captured by
    /// `sens!(........)`. The characters are validated only to construct the
    /// eight bits; they are not a second representation or identity.
    ///
    /// Public only because an exported macro may expand in another crate.
    /// It is not a user-facing constructor; use `sens!(00001100)`.
    #[doc(hidden)]
    pub const fn __from_macro_bits(bits: &str) -> Self {
        let bytes = bits.as_bytes();
        assert!(
            bytes.len() == 8,
            "sens! requires exactly eight bare binary digits"
        );

        let mut packed = 0u8;
        let mut index = 0usize;
        while index < 8 {
            let byte = bytes[index];
            assert!(
                byte == b'0' || byte == b'1',
                "sens! accepts only eight bare 0/1 digits"
            );
            packed = (packed << 1) | (byte - b'0');
            index += 1;
        }

        Self(packed)
    }

    /// Reader-side construction of Sens8 from exactly eight 0/1 source characters.
    pub(crate) const fn from_exact_bits(bits: &str) -> Option<Self> {
        let bytes = bits.as_bytes();
        if bytes.len() != 8 {
            return None;
        }

        let mut packed = 0u8;
        let mut index = 0usize;
        while index < 8 {
            let byte = bytes[index];
            if byte != b'0' && byte != b'1' {
                return None;
            }
            packed = (packed << 1) | (byte - b'0');
            index += 1;
        }

        Some(Self(packed))
    }

    /// Mechanical boundary for serialization/dispatch only.
    pub(crate) const fn from_packed_byte(byte: u8) -> Self {
        Self(byte)
    }

    /// Mechanical boundary for serialization/dispatch only.
    pub(crate) const fn packed_byte(self) -> u8 {
        self.0
    }
}

impl fmt::Display for Sens8 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:08b}", self.0)
    }
}

impl fmt::Debug for Sens8 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Sens8({self})")
    }
}

/// Canonical constructor macro for eight-bit function sense (СЕНС).
///
/// ```
/// let s = sens::sens!(00000011);
/// assert_eq!(s.to_string(), "00000011");
/// ```
#[macro_export]
macro_rules! sens {
    ($bits:literal) => {{
        const SENS: $crate::Sens8 =
            $crate::Sens8::__from_macro_bits(stringify!($bits));
        SENS
    }};
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_eight_bits_round_trip() {
        let s = crate::sens!(00001100);
        assert_eq!(s.to_string(), "00001100");
        assert_eq!(format!("{s:?}"), "Sens8(00001100)");
    }

    #[test]
    fn reader_constructor_accepts_only_exact_eight_bits() {
        assert_eq!(
            Sens8::from_exact_bits("00001100"),
            Some(crate::sens!(00001100))
        );
        assert_eq!(Sens8::from_exact_bits("0000110"), None);
        assert_eq!(Sens8::from_exact_bits("000011000"), None);
        assert_eq!(Sens8::from_exact_bits("00001200"), None);
        assert_eq!(Sens8::from_exact_bits("0b001100"), None);
        assert_eq!(Sens8::from_exact_bits("0000_1100"), None);
    }

    #[test]
    fn packed_byte_round_trips() {
        let s = crate::sens!(11111111);
        assert_eq!(Sens8::from_packed_byte(s.packed_byte()), s);
        assert_eq!(s.to_string(), "11111111");
    }

    #[test]
    fn every_possible_byte_round_trips_without_loss() {
        let mut seen = std::collections::HashSet::new();

        for byte in 0u16..=255 {
            let byte = byte as u8;
            let s = Sens8::from_packed_byte(byte);

            assert_eq!(s.packed_byte(), byte);
            assert_eq!(s.to_string(), format!("{byte:08b}"));
            assert!(seen.insert(s.packed_byte()));
        }

        assert_eq!(seen.len(), 256);
    }
}
