//! Legacy exact-eight SENS compatibility carrier.
//!
//! Historical #1344/#1386 replaced the technical acronym `SID` with `sens`
//! while the language still used one universal eight-bit function space.
//! That ontology is superseded by the exact-domain model (#2490/#2817):
//! canonical semantic identity is a binary object together with its exact
//! domain. `Sens8` remains only for compatibility, transport/backend seams,
//! and staged migration of still-eight-bit consumers.
//!
//! An eight-bit payload by itself MUST NOT be interpreted as a Core.D3/D4/D5/D6
//! identity, and no implicit projection from `Sens8` into
//! `CoreDomainIdentity` is provided here.

use std::fmt;

/// Legacy exact-eight compatibility carrier.
///
/// The eight bits are preserved exactly for historical/compatibility users.
/// They are not sufficient to determine canonical SENS semantic identity:
/// the new ontology also requires the exact domain. This type therefore
/// carries no implicit Core.D3/D4/D5/D6 meaning.
///
/// The packed byte remains a runtime/transport mechanism for this legacy
/// carrier and is never a substitute for a domain-qualified identity.
///
/// Deliberately NOT `Ord`/`PartialOrd` (wsm-lazarus owner, 2026-09-23:
/// "треба заборонити математичні операції над нашим сідом" -- mathematical
/// operations on our sens must be forbidden).
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Sens8(pub(crate) u8);

/// Historical compatibility alias for the exact-eight carrier.
///
/// New semantic code should carry an exact domain identity instead of treating
/// this alias as the language-wide identity type.
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

    /// Legacy reader-side construction from exactly eight 0/1 source characters.
    ///
    /// This constructor does not infer or recover a semantic domain.
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

    /// One-way mechanical boundary for serialization/dispatch only.
    ///
    /// This exposes the already-typed function sense as its exact eight
    /// transport bits. The byte is not source syntax, a numeric alias, or
    /// semantic authority. Construction from an arbitrary byte remains
    /// crate-private so external consumers cannot create a second identity
    /// path around the exact-binary reader/macro boundary.
    pub const fn packed_byte(self) -> u8 {
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

/// Compatibility constructor for an exact-eight historical SENS value.
///
/// New domain-qualified semantic code should construct the exact domain carrier
/// directly; this macro intentionally performs no domain inference.
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

