//! Independent, capability-free core of the sens language.
//! Nezalezhne yadro movy sens bez dostupu do mozhlyvostei operatsiinoi systemy.
//! Unabhängiger Sprachkern von sens ohne Zugriff auf Betriebssystemfunktionen.
//!
//! The crate physically contains no OS access: no filesystem, no processes,
//! no sockets. Host capabilities live in the `sens-host` crate and are
//! installed into this core's registry at startup by whichever embedder
//! wants them (the CLI does; WASM does not). See eval/capabilities.rs.


mod bignum;
mod bits;
mod domain_words;
mod packed_bits;
mod binary_framing;
mod environment;
mod error;
pub(crate) mod eval;
mod language_items;
mod parser;
mod presentation;
mod semantic_registry;
mod source_words;
mod source_packing;
pub mod sens;
mod sid;
