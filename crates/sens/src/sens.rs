//! Retired exact-eight SENS carrier (historical scrap).
//!
//! The universal eight-bit function space is superseded by the exact-domain
//! model (#2490/#2817). Semantic identity is now `CoreDomainIdentity`
//! (D1-D9, `crates/sens/src/domain_identity.rs`) / `DomainIdentity` (D1-D10).
//!
//! The legacy `Sens8(u8)` type and its `sens!`/`packed_byte` API are retired:
//! an eight-bit payload alone is never a domain identity. `Sens8`/`Sens` remain
//! only as aliases so still-migrating consumers name the domain carrier.

pub use crate::domain_identity::CoreDomainIdentity;

/// Retired alias -- the carrier is the exact-domain identity.
pub type Sens8 = CoreDomainIdentity;

/// Retired historical alias.
pub type Sens = CoreDomainIdentity;
