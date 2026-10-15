//! Shared, feature-gated host access to the sterile Zig transport ABI.
//!
//! Keeping this module in the crate library avoids compiling one private
//! copy into every CLI target. All semantics remain owned by `sens`.
//! No fallback path exists when the Zig transport feature is disabled.

#[cfg(feature = "zig-transport")]
pub mod zig_transport;
