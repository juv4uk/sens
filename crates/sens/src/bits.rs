//! Small exact-width binary carriers for the bounded 1..=8-bit fast path.
//!
//! This module owns representation only. A `Bits<N>` value proves that the
//! payload fits exactly within the declared width `N`; it does not assign any
//! SENS meaning to that payload.
//!
//! Width is part of the Rust type:
//!
//! ```compile_fail
//! use sens::{Bit1, Bit2};
//!
//! let one = Bit1::new(1).unwrap();
//! let _: Bit2 = one;
//! ```
//!
//! The universal no-width-ceiling identity carrier is a separate migration
//! concern. This type is deliberately the allocation-free small-word mechanism.

/// Exact-width binary payload for the bounded 1..=8-bit fast path.
///
/// The inner byte is private so safe construction cannot silently truncate,
/// mask, widen, or zero-pad a word. No arithmetic/ordering traits are provided:
/// the carrier proves shape, not semantics.
#[repr(transparent)]
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
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
    /// Construct a word only when both the type width and payload are valid.
    ///
    /// Width zero and widths above eight are intentionally unconstructible
    /// through this bounded carrier.
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

    /// The exact width carried by this Rust type.
    pub const fn width() -> usize {
        N
    }

    /// Mechanical packed payload.
    ///
    /// This loses width if detached from its `Bits<N>` type, so callers must
    /// not use the returned byte as a cross-width semantic identity.
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::mem::size_of;

    fn assert_width<const N: usize>() {
        let max = Bits::<N>::max_value().expect("test width must be valid");

        for raw in 0..=max {
            let word = Bits::<N>::new(raw).expect("in-range payload must construct");
            assert_eq!(word.packed_bits(), raw);
            assert_eq!(Bits::<N>::width(), N);
        }

        if N < 8 {
            assert!(Bits::<N>::new(max + 1).is_none());
        }
    }

    fn assert_append_parent<const N: usize, const M: usize>() {
        let max = Bits::<N>::max_value().expect("test width must be valid");

        for raw in 0..=max {
            let word = Bits::<N>::new(raw).expect("source word must construct");

            for bit in [false, true] {
                let child = word
                    .append::<M>(bit)
                    .expect("adjacent-width append must succeed");
                let parent = child
                    .parent::<N>()
                    .expect("adjacent-width parent must succeed");

                assert_eq!(parent.packed_bits(), raw);
                assert!(word.is_prefix_of(child));
                assert_eq!(child.bit(M - 1), Some(bit));
            }
        }
    }

    #[test]
    fn every_small_width_accepts_exactly_its_range() {
        assert_width::<1>();
        assert_width::<2>();
        assert_width::<3>();
        assert_width::<4>();
        assert_width::<5>();
        assert_width::<6>();
        assert_width::<7>();
        assert_width::<8>();
    }

    #[test]
    fn unsupported_widths_fail_closed() {
        assert!(Bits::<0>::new(0).is_none());
        assert!(Bits::<9>::new(0).is_none());
        assert!(Bits::<{ usize::MAX }>::new(0).is_none());
    }

    #[test]
    fn append_and_parent_are_inverse_on_the_bounded_fast_path() {
        assert_append_parent::<1, 2>();
        assert_append_parent::<2, 3>();
        assert_append_parent::<3, 4>();
        assert_append_parent::<4, 5>();
        assert_append_parent::<5, 6>();
        assert_append_parent::<6, 7>();
        assert_append_parent::<7, 8>();
    }

    #[test]
    fn non_adjacent_or_overflowing_width_changes_are_rejected() {
        let word = Bit3::new(0b101).unwrap();
        assert!(word.append::<3>(true).is_none());
        assert!(word.append::<5>(true).is_none());

        let byte = Bit8::new(0xff).unwrap();
        assert!(byte.append::<8>(true).is_none());

        assert!(word.parent::<1>().is_none());
        assert!(Bit1::new(1).unwrap().parent::<0>().is_none());
    }

    #[test]
    fn prefix_extension_preserves_bit_order_without_semantic_labels() {
        let root = Bit3::new(0b101).unwrap();
        let child0 = root.append::<4>(false).unwrap();
        let child1 = root.append::<4>(true).unwrap();

        assert_eq!(child0.packed_bits(), 0b1010);
        assert_eq!(child1.packed_bits(), 0b1011);
        assert!(root.is_prefix_of(child0));
        assert!(root.is_prefix_of(child1));
        assert!(!child0.is_prefix_of(child1));
    }

    #[test]
    fn bit_index_is_most_significant_first() {
        let word = Bit3::new(0b101).unwrap();
        assert_eq!(word.bit(0), Some(true));
        assert_eq!(word.bit(1), Some(false));
        assert_eq!(word.bit(2), Some(true));
        assert_eq!(word.bit(3), None);
    }

    #[test]
    fn every_bounded_box_occupies_one_host_byte() {
        assert_eq!(size_of::<Bit1>(), 1);
        assert_eq!(size_of::<Bit2>(), 1);
        assert_eq!(size_of::<Bit3>(), 1);
        assert_eq!(size_of::<Bit4>(), 1);
        assert_eq!(size_of::<Bit5>(), 1);
        assert_eq!(size_of::<Bit6>(), 1);
        assert_eq!(size_of::<Bit7>(), 1);
        assert_eq!(size_of::<Bit8>(), 1);
    }
}
