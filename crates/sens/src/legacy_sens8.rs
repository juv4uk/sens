//! Explicit compatibility wrapper for the historical exact-eight-bit carrier.
//!
//! This module is intentionally outside the exact-domain carrier layer.
//! Legacy eight-bit identity may survive at transport/backend boundaries during
//! migration, but it is not canonical domain identity.

use crate::Sens8;

/// Historical exact-eight-bit identity, explicitly marked compatibility-only.
#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct LegacySens8(Sens8);

impl LegacySens8 {
    /// Explicit entry from the historical carrier.
    pub const fn from_sens8(value: Sens8) -> Self {
        Self(value)
    }

    /// Convenience for bounded compatibility tests/adapters.
    pub const fn from_packed_byte(value: u8) -> Self {
        Self(Sens8::from_packed_byte(value))
    }

    /// Recover the historical carrier only at an explicit compatibility edge.
    pub const fn sens8(self) -> Sens8 {
        self.0
    }

    pub const fn packed_byte(self) -> u8 {
        self.0.packed_byte()
    }
}

impl core::fmt::Debug for LegacySens8 {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(formatter, "LegacySens8({})", self.0)
    }
}
