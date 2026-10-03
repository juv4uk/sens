//! Explicit compatibility boundary for the historical exact-eight-bit carrier.
//!
//! This module is intentionally separate from exact-width domain carriers.
//! `Sens8` survives here only as a named migration/transport projection; it
//! is not a canonical callable identity.

use crate::Sens8;
use std::fmt;

#[repr(transparent)]
#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct LegacySens8(Sens8);

impl LegacySens8 {
    /// Explicitly enter the historical compatibility lane.
    pub const fn from_sens8(value: Sens8) -> Self {
        Self(value)
    }

    /// Explicitly recover the historical carrier for an old backend/registry.
    pub const fn sens8(self) -> Sens8 {
        self.0
    }

    /// Mechanical byte projection for legacy FASL/wire only.
    pub const fn packed_byte(self) -> u8 {
        self.0.packed_byte()
    }

    /// Mechanical decoder used only by compatibility transport.
    pub(crate) const fn from_packed_byte(value: u8) -> Self {
        Self(Sens8::from_packed_byte(value))
    }

    /// Reader-side compatibility decoder for exactly eight written bits.
    pub(crate) const fn from_exact_bits(bits: &str) -> Option<Self> {
        match Sens8::from_exact_bits(bits) {
            Some(value) => Some(Self(value)),
            None => None,
        }
    }
}

impl fmt::Display for LegacySens8 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

impl fmt::Debug for LegacySens8 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "LegacySens8({})", self.0)
    }
}
