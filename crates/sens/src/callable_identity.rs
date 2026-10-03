//! Domain-qualified callable identity for the live Core migration.
//!
//! Canonical callable identity is no longer a universal eight-bit box.
//! D3/D4/D5/D6 remain distinct even when their packed payloads are equal.
//! Historical Sens8 survives only as an explicitly named compatibility form
//! while evaluator/registry consumers are migrated in later #2817 slices.

use crate::domain_words::{Bija3, CoreD4, CoreD5, CoreD6, DomainWord};
use crate::Sens8;
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

    /// Explicit compatibility projection for the historical exact-8 runtime.
    ///
    /// This variant is not equal to any D3..D6 identity and has no implicit
    /// zero-extension/truncation conversion.
    LegacySens8(Sens8),
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

    /// Enter the old exact-eight mechanism explicitly.
    pub const fn from_legacy_sens8(value: Sens8) -> Self {
        Self::LegacySens8(value)
    }

    /// Exact domain width. Width stays attached to identity.
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
            Self::LegacySens8(_) => 8,
        }
    }

    /// Mechanical payload only; never sufficient as semantic identity.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
            Self::LegacySens8(value) => value.packed_byte(),
        }
    }

    /// Domain-qualified Core word, when this is a live exact-width Core object.
    pub const fn domain_word(self) -> Option<DomainWord> {
        match self {
            Self::D3(value) => Some(DomainWord::D3(value)),
            Self::D4(value) => Some(DomainWord::D4(value)),
            Self::D5(value) => Some(DomainWord::D5(value)),
            Self::D6(value) => Some(DomainWord::D6(value)),
            Self::LegacySens8(_) => None,
        }
    }

    /// Historical mechanism projection, available only for the explicit
    /// compatibility variant. Domain-qualified identities never zero-extend.
    pub const fn legacy_sens8(self) -> Option<Sens8> {
        match self {
            Self::LegacySens8(value) => Some(value),
            Self::D3(_) | Self::D4(_) | Self::D5(_) | Self::D6(_) => None,
        }
    }

    pub const fn is_legacy(self) -> bool {
        matches!(self, Self::LegacySens8(_))
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
            Self::LegacySens8(_) => "LegacySens8",
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
    fn legacy_exact8_never_equals_short_domain_identity() {
        let d3 = CallableDomainId::d3(Bija3::from_word(Bit3::new(0b101).unwrap()));
        let legacy = CallableDomainId::from_legacy_sens8(
            Sens8::from_packed_byte(0b0000_0101),
        );

        assert_eq!(d3.packed_bits(), legacy.packed_bits());
        assert_ne!(d3, legacy);
        assert_eq!(d3.legacy_sens8(), None);
        assert_eq!(legacy.legacy_sens8(), Some(Sens8::from_packed_byte(5)));
    }

    #[test]
    fn only_domain_qualified_variants_expose_domain_word() {
        let d4 = CallableDomainId::d4(CoreD4::from_word(Bit4::new(0b0010).unwrap()));
        let legacy =
            CallableDomainId::from_legacy_sens8(Sens8::from_packed_byte(0b0000_0010));

        assert!(matches!(d4.domain_word(), Some(DomainWord::D4(_))));
        assert_eq!(legacy.domain_word(), None);
    }
}
