//! Domain-qualified callable identity.
//!
//! Domain is part of identity. Equal payload bits in different callable
//! domains never collapse. D1 predicate answers, D2 structure, and D7
//! sound/ordinal are deliberately absent.

use crate::{Bija3, CoreD4, CoreD5, CoreD6, LegacySens8};
use std::fmt;

#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableDomainId {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
    Legacy8(LegacySens8),
}

impl CallableDomainId {
    pub const fn d3(value: Bija3) -> Self { Self::D3(value) }
    pub const fn d4(value: CoreD4) -> Self { Self::D4(value) }
    pub const fn d5(value: CoreD5) -> Self { Self::D5(value) }
    pub const fn d6(value: CoreD6) -> Self { Self::D6(value) }

    /// Explicit compatibility admission; there is deliberately no conversion
    /// from a raw byte or implicit equality with historical identity.
    pub const fn legacy(value: LegacySens8) -> Self { Self::Legacy8(value) }

    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::Legacy8(_) => 8,
        }
    }

    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(word) => word.word().packed_bits(),
            Self::D4(word) => word.word().packed_bits(),
            Self::D5(word) => word.word().packed_bits(),
            Self::D6(word) => word.word().packed_bits(),
            Self::Legacy8(word) => word.packed_byte(),
        }
    }

    /// Compatibility extraction is explicit and succeeds only for Legacy8.
    pub const fn legacy(self) -> Option<LegacySens8> {
        match self {
            Self::Legacy8(value) => Some(value),
            Self::D3(_) | Self::D4(_) | Self::D5(_) | Self::D6(_) => None,
        }
    }
}

impl From<Bija3> for CallableDomainId {
    fn from(value: Bija3) -> Self { Self::D3(value) }
}
impl From<CoreD4> for CallableDomainId {
    fn from(value: CoreD4) -> Self { Self::D4(value) }
}
impl From<CoreD5> for CallableDomainId {
    fn from(value: CoreD5) -> Self { Self::D5(value) }
}
impl From<CoreD6> for CallableDomainId {
    fn from(value: CoreD6) -> Self { Self::D6(value) }
}

impl fmt::Display for CallableDomainId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::D3(_) => write!(f, "d3:{:03b}", self.packed_bits()),
            Self::D4(_) => write!(f, "d4:{:04b}", self.packed_bits()),
            Self::D5(_) => write!(f, "d5:{:05b}", self.packed_bits()),
            Self::D6(_) => write!(f, "d6:{:06b}", self.packed_bits()),
            Self::Legacy8(value) => value.fmt(f),
        }
    }
}

impl fmt::Debug for CallableDomainId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::D3(_) => write!(f, "CallableDomainId::D3({:03b})", self.packed_bits()),
            Self::D4(_) => write!(f, "CallableDomainId::D4({:04b})", self.packed_bits()),
            Self::D5(_) => write!(f, "CallableDomainId::D5({:05b})", self.packed_bits()),
            Self::D6(_) => write!(f, "CallableDomainId::D6({:06b})", self.packed_bits()),
            Self::Legacy8(value) => write!(f, "CallableDomainId::Legacy8({value})"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit3, Bit4, Bit5, Bit6};
    use std::collections::HashSet;

    #[test]
    fn same_payload_stays_distinct_across_callable_domains() {
        let d3 = SelfId::d3(Bija3::from_word(Bit3::new(1).unwrap()));
        let d4 = SelfId::d4(CoreD4::from_word(Bit4::new(1).unwrap()));
        let d5 = SelfId::d5(CoreD5::from_word(Bit5::new(1).unwrap()));
        let d6 = SelfId::d6(CoreD6::from_word(Bit6::new(1).unwrap()));
        let ids = HashSet::from([d3, d4, d5, d6]);
        assert_eq!(ids.len(), 4);
        assert_eq!([d3.width(), d4.width(), d5.width(), d6.width()], [3,4,5,6]);
        assert_eq!([d3.packed_bits(), d4.packed_bits(), d5.packed_bits(), d6.packed_bits()], [1,1,1,1]);
    }

    type SelfId = CallableDomainId;

    #[test]
    fn legacy_is_a_distinct_explicit_variant() {
        let typed = SelfId::d3(Bija3::from_word(Bit3::new(5).unwrap()));
        let legacy = SelfId::legacy(LegacySens8::from_packed_byte(5));
        assert_ne!(typed, legacy);
        assert!(typed.legacy().is_none());
        assert_eq!(legacy.legacy().unwrap().packed_byte(), 5);
    }
}
