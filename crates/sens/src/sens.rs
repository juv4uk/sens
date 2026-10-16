//! The `sens!` macro belonged to the historical exact-eight carrier.
//!
//! It is removed: the canonical semantic identity is the exact-domain carrier
//! `CoreDomainIdentity` (D1-D9, `crates/sens/src/domain_identity.rs`). No
//! historical eight-bit carrier remains in the runtime.

pub use crate::domain_identity::CoreDomainIdentity;
