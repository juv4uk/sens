//! sens-core -- the CLEAN SENS core, built WITHOUT the junk.
//!
//! Contains only the modules that do not pull the staged-out set (packing, reader, Rust math).
//! Physical bit-packing is the sterile Zig corridor's job; the domain-ladder reader is the SENS
//! REPL's job; arithmetic is SENS's job. This crate is the carrier + domain words and nothing else.

pub mod bit9;
pub mod bootstrap_measurement;
pub mod domain_owner_generated;
pub mod error;
pub mod program_data;
pub mod sens;
