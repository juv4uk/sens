use std::fmt;

/// Exact eight-bit semantic identity.
///
/// The canonical identity is the bit spelling itself (`00000000..11111111`).
/// The packed byte is a private runtime/transport mechanism and is never the
/// public semantic name of the SID.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Sid8(u8);

impl Sid8 {
    /// Macro-only constructor from the exact token spelling captured by
    /// `sid!(........)`. This deliberately validates text instead of asking
    /// Rust to evaluate the token as a number.
    ///
    /// Public only because an exported macro may expand in another crate.
    /// It is not a user-facing constructor; use `sid!(00001100)`.
    #[doc(hidden)]
    pub const fn __from_macro_spelling(spelling: &str) -> Self {
        let bytes = spelling.as_bytes();
        assert!(
            bytes.len() == 8,
            "sid! requires exactly eight bare binary digits"
        );

        let mut packed = 0u8;
        let mut index = 0usize;
        while index < 8 {
            let byte = bytes[index];
            assert!(
                byte == b'0' || byte == b'1',
                "sid! accepts only eight bare 0/1 digits"
            );
            packed = (packed << 1) | (byte - b'0');
            index += 1;
        }

        Self(packed)
    }

    /// Reader-side construction from canonical my-lisp SID spelling.
    pub(crate) const fn from_canonical_spelling(spelling: &str) -> Option<Self> {
        let bytes = spelling.as_bytes();
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

impl fmt::Display for Sid8 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:08b}", self.0)
    }
}

impl fmt::Debug for Sid8 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Sid8({self})")
    }
}

/// Construct an exact-width SID from the literal token spelling itself.
///
/// The macro never asks Rust for the token's numeric value. `stringify!`
/// captures the spelling and the const constructor validates exactly eight
/// bare `0`/`1` characters at compile time.
#[macro_export]
macro_rules! sid {
    ($bits:literal) => {{
        const SID: $crate::Sid8 =
            $crate::Sid8::__from_macro_spelling(stringify!($bits));
        SID
    }};
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_spelling_round_trips_without_decimal_identity() {
        let sid = crate::sid!(00001100);
        assert_eq!(sid.to_string(), "00001100");
        assert_eq!(format!("{sid:?}"), "Sid8(00001100)");
    }

    #[test]
    fn reader_constructor_accepts_only_exact_eight_bits() {
        assert_eq!(
            Sid8::from_canonical_spelling("00001100"),
            Some(crate::sid!(00001100))
        );
        assert_eq!(Sid8::from_canonical_spelling("0000110"), None);
        assert_eq!(Sid8::from_canonical_spelling("000011000"), None);
        assert_eq!(Sid8::from_canonical_spelling("00001200"), None);
        assert_eq!(Sid8::from_canonical_spelling("0b001100"), None);
        assert_eq!(Sid8::from_canonical_spelling("0000_1100"), None);
    }

    #[test]
    fn packed_byte_is_only_a_round_trip_mechanism() {
        let sid = crate::sid!(11111111);
        assert_eq!(Sid8::from_packed_byte(sid.packed_byte()), sid);
        assert_eq!(sid.to_string(), "11111111");
    }
}
