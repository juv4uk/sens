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

pub mod lower;

pub use lower::{LowerError, lower_expr};

use crate::DomainIdentity;

// Phase 2 in progress: porting lower.rs functions from CML (1046 lines)
// See: docs/research/2026-10-06-compiler-migration-plan.md
//
// Dispatcher: every function is a D3 or D4 exact bit pattern
//   D3:001 (1)  = QUOTE
//   D3:010 (2)  = ATOM?
//   D3:011 (3)  = CDR
//   D3:100 (4)  = CAR
//   D3:101 (5)  = EQ?
//   D3:110 (6)  = COND
//   D3:111 (7)  = CONS
//   D4:0010 (2) = LAMBDA
//   D4:0011 (3) = DEFINE
// All other identities are rejected; backends are separate authority.

pub mod entry {
    //! Bootstrap entry points (Phase 2 complete)
}
