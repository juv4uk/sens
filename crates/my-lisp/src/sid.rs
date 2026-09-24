use std::fmt;

/// Exact eight-bit semantic identity.
///
/// The function identity is exactly the eight bits themselves (`00000000..11111111`).
/// The packed byte is a private runtime/transport mechanism and is never the
/// alternate identity of the SID.
///
/// Deliberately NOT `Ord`/`PartialOrd` (wsm-lazarus owner, 2026-09-23:
/// "треба заборонити математичні операції над нашим сідом" -- mathematical
/// operations on our SID must be forbidden). `Ord`/`PartialOrd` were derived
/// here until this commit with zero actual use anywhere in this codebase
/// (verified by search), meaning `sid1 < sid2`, `.sort()`, and
/// `BTreeMap<Sid8, _>`/`BTreeSet<Sid8>` all compiled and worked with no
/// `unsafe` at all -- treating an opaque identity as a numerically ordered
/// quantity, exactly the same class of gap wsm-lazarus's TSid8 closed on
/// the Pascal side (there, the exploit was a same-size `Byte(sid)` ordinal
/// typecast bypassing `strict private`; here, it was simply available for
/// free via `derive`). `Eq`/`Hash`/`PartialEq` remain: identity comparison
/// and use as a hash-map/hash-set key are the only meaningful operations on
/// a SID, matching TSid8's own `=`/`<>` and nothing else.
///
/// ```
/// let a = my_lisp::sid!(00000001);
/// let b = my_lisp::sid!(00000010);
/// assert!(a != b);
/// assert_eq!(a, my_lisp::sid!(00000001));
/// ```
///
/// No ordering or arithmetic operator exists on `Sid8` at all -- each of
/// these fails to compile, not merely at runtime:
///
/// ```compile_fail
/// let a = my_lisp::sid!(00000001);
/// let b = my_lisp::sid!(00000010);
/// let _ = a < b;
/// ```
///
/// ```compile_fail
/// let a = my_lisp::sid!(00000001);
/// let b = my_lisp::sid!(00000010);
/// let _ = a > b;
/// ```
///
/// ```compile_fail
/// let a = my_lisp::sid!(00000001);
/// let b = my_lisp::sid!(00000010);
/// let _ = a + b;
/// ```
///
/// ```compile_fail
/// let a = my_lisp::sid!(00000001);
/// let b = my_lisp::sid!(00000010);
/// let _ = a - b;
/// ```
///
/// ```compile_fail
/// let a = my_lisp::sid!(00000001);
/// let b = my_lisp::sid!(00000010);
/// let _ = a * b;
/// ```
///
/// ```compile_fail
/// let mut v = vec![my_lisp::sid!(00000010), my_lisp::sid!(00000001)];
/// v.sort();
/// ```
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Sid8(u8);

impl Sid8 {
    /// Macro-only bridge from exactly eight source 0/1 characters captured by
    /// `sid!(........)`. The characters are validated only to construct the
    /// eight bits; they are not a second SID representation or identity.
    ///
    /// Public only because an exported macro may expand in another crate.
    /// It is not a user-facing constructor; use `sid!(00001100)`.
    #[doc(hidden)]
    pub const fn __from_macro_bits(bits: &str) -> Self {
        let bytes = bits.as_bytes();
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

    /// Reader-side construction of Sid8 from exactly eight 0/1 source characters.
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

/// Construct one exact eight-bit function identity.
///
/// The macro never uses a decimal or prefixed numeric identity. `stringify!`
/// is only a Rust macro bridge: the const constructor accepts exactly eight
/// `0`/`1` source characters and returns Sid8.
///
/// ```
/// let sid = my_lisp::sid!(00001100);
/// assert_eq!(sid.to_string(), "00001100");
/// ```
///
/// Wrong width, numeric prefixes, separators, suffixes and quoted strings are
/// compile-time errors rather than alternate identities.
///
/// ```compile_fail
/// let _ = my_lisp::sid!(0000110);
/// ```
///
/// ```compile_fail
/// let _ = my_lisp::sid!(0b00001100);
/// ```
///
/// ```compile_fail
/// let _ = my_lisp::sid!(0000_1100);
/// ```
///
/// ```compile_fail
/// let _ = my_lisp::sid!(00001100u8);
/// ```
///
/// ```compile_fail
/// let _ = my_lisp::sid!("00001100");
/// ```
#[macro_export]
macro_rules! sid {
    ($bits:literal) => {{
        const SID: $crate::Sid8 =
            $crate::Sid8::__from_macro_bits(stringify!($bits));
        SID
    }};
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_eight_bits_round_trip_without_decimal_identity() {
        let sid = crate::sid!(00001100);
        assert_eq!(sid.to_string(), "00001100");
        assert_eq!(format!("{sid:?}"), "Sid8(00001100)");
    }

    #[test]
    fn reader_constructor_accepts_only_exact_eight_bits() {
        assert_eq!(
            Sid8::from_exact_bits("00001100"),
            Some(crate::sid!(00001100))
        );
        assert_eq!(Sid8::from_exact_bits("0000110"), None);
        assert_eq!(Sid8::from_exact_bits("000011000"), None);
        assert_eq!(Sid8::from_exact_bits("00001200"), None);
        assert_eq!(Sid8::from_exact_bits("0b001100"), None);
        assert_eq!(Sid8::from_exact_bits("0000_1100"), None);
    }

    #[test]
    fn packed_byte_is_only_a_round_trip_mechanism() {
        let sid = crate::sid!(11111111);
        assert_eq!(Sid8::from_packed_byte(sid.packed_byte()), sid);
        assert_eq!(sid.to_string(), "11111111");
    }

    /// Exhaustive u8 non-loss proof (owner, 2026-09-23: "чи всюди сід це
    /// 8-бітне двійкове і чи десь це не втрачається" -- whether SID is
    /// 8-bit binary everywhere, and whether it's lost somewhere).
    /// Every one of the 256 possible byte values survives
    /// from_packed_byte -> packed_byte unchanged, renders as the exact
    /// eight-character binary spelling matching that byte, and is
    /// pairwise distinct from every other value -- Sid8 is total and
    /// faithful across the full closed domain, not narrowed or lossy
    /// anywhere in this round trip.
    #[test]
    fn every_possible_byte_round_trips_through_sid8_without_loss() {
        let mut seen = std::collections::HashSet::new();

        for byte in 0u16..=255 {
            let byte = byte as u8;
            let sid = Sid8::from_packed_byte(byte);

            assert_eq!(
                sid.packed_byte(),
                byte,
                "byte {byte:#010b} did not round-trip through Sid8 unchanged"
            );
            assert_eq!(
                sid.to_string(),
                format!("{byte:08b}"),
                "byte {byte:#010b} rendered as bits different from its own identity"
            );
            assert!(
                seen.insert(sid.packed_byte()),
                "byte {byte:#010b} collided with a previously seen SID -- domain is not faithfully total"
            );
        }

        assert_eq!(seen.len(), 256, "all 256 possible SID8 values must be distinct and reachable");
    }
}
