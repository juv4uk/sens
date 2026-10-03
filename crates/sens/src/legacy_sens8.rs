//! Explicit compatibility wrapper for the historical exact-eight-bit carrier.
//!
//! This module is intentionally boring: it exists only so old transport and
//! backend paths can remain named compatibility mechanisms while canonical
//! semantic identity moves to exact domains.

/// Historical exact-eight compatibility identity.
///
/// Never infer a Core domain from this byte. Never compare it to a domain
/// identity by packed payload.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct LegacySens8(crate::Sens8);

impl LegacySens8 {
    pub const fn from_sens8(value: crate::Sens8) -> Self {
        Self(value)
    }

    pub const fn sens8(self) -> crate::Sens8 {
        self.0
    }

    /// Compatibility-only byte entry used by old transport/backend paths.
    pub const fn from_packed_byte(value: u8) -> Self {
        Self(crate::Sens8::from_packed_byte(value))
    }

    pub const fn packed_byte(self) -> u8 {
        self.0.packed_byte()
    }
}

impl std::fmt::Debug for LegacySens8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "LegacySens8({})", self.0)
    }
}

impl std::fmt::Display for LegacySens8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(formatter)
    }
}
