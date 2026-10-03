//! Runtime call-head identity during the Sens8/Sid8 exit.
//!
//! The canonical Core coordinate is carried by `CoreDomainIdentity`; this
//! module does not define a second D3/D4/D5/D6 ontology. `Legacy8` is an
//! explicitly tagged compatibility mechanism for old exact-eight paths.

use crate::{CoreDomainIdentity, LegacySens8};

#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub enum CallableDomainId {
    /// Canonical exact-domain identity. Executability is still decided by SENS
    /// laws/owner maps; constructing this carrier does not admit a resident.
    Domain(CoreDomainIdentity),
    /// Historical exact-eight compatibility only.
    Legacy8(LegacySens8),
}

impl CallableDomainId {
    pub const fn from_domain(identity: CoreDomainIdentity) -> Self {
        Self::Domain(identity)
    }

    /// Named compatibility entry. The exact-width module never sees Sens8
    /// directly; byte conversion is confined to the compatibility module.
    pub const fn from_legacy(value: LegacySens8) -> Self {
        Self::Legacy8(value)
    }

    pub const fn width(self) -> usize {
        match self {
            Self::Domain(identity) => identity.width(),
            Self::Legacy8(_) => 8,
        }
    }

    /// Mechanical payload only. The enum variant remains part of identity.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::Domain(identity) => identity.packed_bits(),
            Self::Legacy8(value) => value.packed_byte(),
        }
    }

    pub const fn domain(self) -> Option<CoreDomainIdentity> {
        match self {
            Self::Domain(identity) => Some(identity),
            Self::Legacy8(_) => None,
        }
    }

    /// Only the explicit compatibility variant can recover the opaque legacy
    /// wrapper. Converting that wrapper to Sens8 is a boundary-layer action.
    pub const fn legacy(self) -> Option<LegacySens8> {
        match self {
            Self::Domain(_) => None,
            Self::Legacy8(value) => Some(value),
        }
    }
}

impl From<CoreDomainIdentity> for CallableDomainId {
    fn from(value: CoreDomainIdentity) -> Self {
        Self::Domain(value)
    }
}

impl std::fmt::Display for CallableDomainId {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            formatter,
            "{:0width$b}",
            self.packed_bits(),
            width = self.width()
        )
    }
}

impl std::fmt::Debug for CallableDomainId {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Domain(identity) => write!(formatter, "CallableDomainId::{identity:?}"),
            Self::Legacy8(value) => write!(formatter, "CallableDomainId::Legacy8({value})"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Bit4, CoreD4};

    #[test]
    fn equal_payload_domain_and_legacy_never_collapse() {
        let d3 = CallableDomainId::from_domain(CoreDomainIdentity::from(
            Bija3::from_word(Bit3::new(1).unwrap()),
        ));
        let d4 = CallableDomainId::from_domain(CoreDomainIdentity::from(
            CoreD4::from_word(Bit4::new(1).unwrap()),
        ));
        let legacy = CallableDomainId::from_legacy(LegacySens8::from_packed_byte(1));

        assert_eq!(d3.packed_bits(), 1);
        assert_eq!(d4.packed_bits(), 1);
        assert_eq!(legacy.packed_bits(), 1);
        assert_ne!(d3, d4);
        assert_ne!(d3, legacy);
        assert_ne!(d4, legacy);
        assert!(d3.legacy().is_none());
        assert!(d4.legacy().is_none());
        assert_eq!(legacy.legacy().unwrap().packed_byte(), 1);
    }

    #[test]
    fn callable_wrapper_does_not_redefine_domain_identity() {
        let domain = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b101).unwrap()));
        let callable = CallableDomainId::from_domain(domain);

        assert_eq!(callable.domain(), Some(domain));
        assert_eq!(callable.width(), 3);
        assert_eq!(callable.to_string(), "101");
    }
}
