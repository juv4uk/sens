//! Compiler lowering: `ast::Expr` → SENS semantic IR, working with exact DomainIdentity.
//!
//! This module is the migration of `cml/src/lower.rs` into SENS, rewritten to consume
//! and produce `DomainIdentity` instead of legacy `Sid8`.
//!
//! Historical context: `lower.rs` in cml used a parallel `Sid8` identity layer alongside
//! the compiler's decision logic. This version uses SENS-native `DomainIdentity` throughout,
//! with exact domain and width as part of every identity, never as decorative metadata.
//!
//! Authority: D3 law ratified sens#3202, D4 contract ratified sens#3272, Contract 11.6.

use crate::DomainIdentity;

// TODO Phase 2: port lower.rs functions, removing all Sid8 references
// See: docs/research/2026-10-06-compiler-migration-plan.md

pub mod entry {
    //! Placeholder for lower_program, lower_expr entry points (Phase 2)
}
