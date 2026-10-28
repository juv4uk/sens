//! Exact-width logical binary words for SENS.
//!
//! A `Bits<N>` value is a transient semantic word used at typed boundaries.
//! It proves that a payload has exactly width `N`; it is **not** the canonical
//! physical storage for a program. Rust's ABI is byte-addressed, so a standalone
//! runtime value cannot occupy less than one byte. SENS does not use that host
//! fact as semantic width and must not treat one `Bits<N>` object as one
//! physical program cell.
//!
//! Canonical program storage is built separately by `BitPacker`/
//! `PackedBitstream`, where multiple domains are concatenated at the bit level
//! and physical bytes are emitted only for the surrounding program payload.

/// Exact-width logical binary payload for a bounded 1..=8-bit word.
///
/// The private byte is only a transient host register for carrying an already
/// validated word into typed/domain logic. It is never the canonical storage
/// model for a sequence of SENS values: program storage is bit-packed by
/// `BitPacker`.
///
/// Width is part of the Rust type:
///
/// ```compile_fail
/// use sens::{Bit1, Bit2};
///
/// let one = Bit1::new(1).unwrap();
/// let _: Bit2 = one;
/// ```
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Bits<const N: usize>(u8);

pub type Bit1 = Bits<1>;
pub type Bit2 = Bits<2>;
pub type Bit3 = Bits<3>;
pub type Bit4 = Bits<4>;
pub type Bit5 = Bits<5>;
pub type Bit6 = Bits<6>;
pub type Bit7 = Bits<7>;
pub type Bit8 = Bits<8>;

impl<const N: usize> Bits<N> {
    /// Construct a logical word only when both the type width and payload are valid.
    ///
    /// Width zero and widths above eight are intentionally unconstructible
    /// through this bounded fast-path carrier.
    pub const fn new(value: u8) -> Option<Self> {
        if N == 0 || N > 8 {
            return None;
        }

        if (value as u16) < (1u16 << N) {
            Some(Self(value))
        } else {
            None
        }
    }

    /// The exact semantic width carried by this Rust type.
    pub const fn width() -> usize {
        N
    }

    /// Mechanical payload extraction for typed logic and packing.
    ///
    /// The returned host byte is only a scratch projection; callers must keep
    /// it qualified by this exact `Bits<N>` type and must not use it as a
    /// cross-width semantic identity.
    pub const fn packed_bits(self) -> u8 {
        self.0
    }

    /// Largest packed payload admitted by this width.
    pub const fn max_value() -> Option<u8> {
        if N == 0 || N > 8 {
            None
        } else {
            Some(((1u16 << N) - 1) as u8)
        }
    }

    /// Read one bit by zero-based index from the most-significant side.
    pub const fn bit(self, index: usize) -> Option<bool> {
        if N == 0 || N > 8 || index >= N {
            return None;
        }

        let shift = N - 1 - index;
        Some(((self.0 >> shift) & 1) != 0)
    }

    /// Append one binary symbol into an explicitly requested next-width type.
    ///
    /// The operation succeeds only for `M == N + 1`. No width inference,
    /// truncation, widening or semantic child law is hidden here.
    pub const fn append<const M: usize>(self, bit: bool) -> Option<Bits<M>> {
        if N == 0 || N >= 8 || M != N + 1 {
            return None;
        }

        Bits::<M>::new((self.0 << 1) | (bit as u8))
    }

    /// Remove the final bit into an explicitly requested previous-width type.
    pub const fn parent<const M: usize>(self) -> Option<Bits<M>> {
        if N <= 1 || N > 8 || M != N - 1 {
            return None;
        }

        Bits::<M>::new(self.0 >> 1)
    }

    /// Mechanical exact-prefix relation; it assigns no semantic relationship.
    pub const fn is_prefix_of<const M: usize>(self, other: Bits<M>) -> bool {
        if N == 0 || N > 8 || M == 0 || M > 8 || N > M {
            return false;
        }

        self.0 == (other.0 >> (M - N))
    }
}

