//! Domain-qualified Core identity key for the Sens8/Sid8 exit.
//!
//! This layer carries identity context only. It does not decide whether a
//! coordinate is occupied, callable, primitive, derived, or generated. Those
//! facts remain owned by SENS domain laws and their executable witnesses.
//!
//! Equal packed payloads in different domains remain different identities:
//! D3 `001` is not D4 `0001`.

use crate::{Bija3, CoreD4, CoreD5, CoreD6};
use std::fmt;

/// Exact domain-qualified identity for the current Core operation domains.
///
/// D1 predicate answers and D2 structure are intentionally absent because this
/// key is for the D3+ Core identity migration. D7 is intentionally absent:
/// sharing a bounded binary representation does not grant Core identity or
/// callability.
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CoreDomainIdentity {
    D3(Bija3),
    D4(CoreD4),
    D5(CoreD5),
    D6(CoreD6),
}

impl fmt::Debug for CoreDomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let width = self.width();
        write!(
            formatter,
            "CoreDomainIdentity<D{width}>({:0width$b})",
            self.packed_bits()
        )
    }
}

impl fmt::Display for CoreDomainIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{:0width$b}",
            self.packed_bits(),
            width = self.width()
        )
    }
}

impl CoreDomainIdentity {
    /// Exact domain width carried by this identity.
    pub const fn width(self) -> usize {
        match self {
            Self::D3(_) => 3,
            Self::D4(_) => 4,
            Self::D5(_) => 5,
            Self::D6(_) => 6,
        }
    }

    /// Mechanical payload inside the exact domain.
    ///
    /// The returned byte is never a standalone identity. Callers must retain
    /// the `CoreDomainIdentity` variant/domain alongside it.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::D3(value) => value.word().packed_bits(),
            Self::D4(value) => value.word().packed_bits(),
            Self::D5(value) => value.word().packed_bits(),
            Self::D6(value) => value.word().packed_bits(),
        }
    }
}

impl From<Bija3> for CoreDomainIdentity {
    fn from(value: Bija3) -> Self {
        Self::D3(value)
    }
}

impl From<CoreD4> for CoreDomainIdentity {
    fn from(value: CoreD4) -> Self {
        Self::D4(value)
    }
}

impl From<CoreD5> for CoreDomainIdentity {
    fn from(value: CoreD5) -> Self {
        Self::D5(value)
    }
}

impl From<CoreD6> for CoreDomainIdentity {
    fn from(value: CoreD6) -> Self {
        Self::D6(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit3, Bit4, Bit5, Bit6};

    #[test]
    fn equal_packed_payloads_in_different_domains_are_distinct_identities() {
        let d3 = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b001).unwrap()));
        let d4 = CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(0b0001).unwrap()));
        let d5 = CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(0b00001).unwrap()));
        let d6 = CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(0b000001).unwrap()));

        assert_eq!(d3.packed_bits(), 1);
        assert_eq!(d4.packed_bits(), 1);
        assert_eq!(d5.packed_bits(), 1);
        assert_eq!(d6.packed_bits(), 1);

        assert!(d3 != d4);
        assert!(d3 != d5);
        assert!(d3 != d6);
        assert!(d4 != d5);
        assert!(d4 != d6);
        assert!(d5 != d6);
    }

    #[test]
    fn exact_domain_width_is_recoverable_without_numeric_inference() {
        let cases = [
            CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b101).unwrap())),
            CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(0b1010).unwrap())),
            CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(0b10101).unwrap())),
            CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(0b101010).unwrap())),
        ];

        assert_eq!(
            cases.map(CoreDomainIdentity::width),
            [3, 4, 5, 6]
        );
    }

    #[test]
    fn every_domain_preserves_its_full_bounded_payload_range() {
        for raw in 0..=7 {
            let id = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(raw).unwrap()));
            assert_eq!(id.width(), 3);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=15 {
            let id = CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(raw).unwrap()));
            assert_eq!(id.width(), 4);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=31 {
            let id = CoreDomainIdentity::from(CoreD5::from_word(Bit5::new(raw).unwrap()));
            assert_eq!(id.width(), 5);
            assert_eq!(id.packed_bits(), raw);
        }
        for raw in 0..=63 {
            let id = CoreDomainIdentity::from(CoreD6::from_word(Bit6::new(raw).unwrap()));
            assert_eq!(id.width(), 6);
            assert_eq!(id.packed_bits(), raw);
        }
    }
}
