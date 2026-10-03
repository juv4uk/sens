//! Domain-qualified callable identity for the live Core migration.
//!
//! Canonical callable identity is no longer a universal eight-bit box.
//! D3/D4/D5/D6 remain distinct even when their packed payloads are equal.
//! Historical Sens8 survives only as an explicitly named compatibility form
//! while evaluator/registry consumers are migrated in later #2817 slices.

use crate::domain_words::{Bija3, CoreD4, CoreD5, CoreD6, DomainWord};
use std::fmt;

/// One callable binary object together with its exact semantic domain.
///
/// D1 predicate answers and D2 structure are intentionally absent: being binary
/// does not make an object callable. D7 is likewise excluded.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableDomainId {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
}

impl CallableDomainId {
    pub const fn d3(value: Bija3) -> Self {
        Self::D3(value)
    }

    pub const fn d4(value: CoreD4) -> Self {
        Self::D4(value)
    }

    pub const fn d5(value: CoreD5) -> Self {
        Self::D5(value)
    }

    pub const fn d6(value: CoreD6) -> Self {
        Self::D6(value)
    }

    /// Exact domain width. Width stays attached to identity.
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
        }
    }

    /// Mechanical payload only; never sufficient as semantic identity.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
        }
    }

    /// Domain-qualified Core word, when this is a live exact-width Core object.
    pub const fn domain_word(self) -> Option<DomainWord> {
        match self {
            Self::D3(value) => Some(DomainWord::D3(value)),
            Self::D4(value) => Some(DomainWord::D4(value)),
            Self::D5(value) => Some(DomainWord::D5(value)),
            Self::D6(value) => Some(DomainWord::D6(value)),
        }
    }

}

impl fmt::Display for CallableDomainId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{:0width$b}",
            self.packed_bits(),
            width = self.width()
        )
    }
}

impl fmt::Debug for CallableDomainId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let domain = match self {
            Self::D3(_) => "Core.D3",
            Self::D4(_) => "Core.D4",
            Self::D5(_) => "Core.D5",
            Self::D6(_) => "Core.D6",
        };
        write!(formatter, "{domain}({self})")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit3, Bit4, Bit5, Bit6};

    #[test]
    fn equal_packed_payloads_do_not_collapse_across_domains() {
        let d3 = CallableDomainId::d3(Bija3::from_word(Bit3::new(1).unwrap()));
        let d4 = CallableDomainId::d4(CoreD4::from_word(Bit4::new(1).unwrap()));
        let d5 = CallableDomainId::d5(CoreD5::from_word(Bit5::new(1).unwrap()));
        let d6 = CallableDomainId::d6(CoreD6::from_word(Bit6::new(1).unwrap()));

        for value in [d3, d4, d5, d6] {
            assert_eq!(value.packed_bits(), 1);
        }
        assert_ne!(d3, d4);
        assert_ne!(d4, d5);
        assert_ne!(d5, d6);
    }

    #[test]
    fn domain_word_round_trip_preserves_callable_domain() {
        let d4 = CallableDomainId::d4(CoreD4::from_word(Bit4::new(0b0010).unwrap()));
        assert!(matches!(d4.domain_word(), Some(DomainWord::D4(_))));
        assert_eq!(d4.width(), 4);
        assert_eq!(d4.to_string(), "0010");
    }
}
