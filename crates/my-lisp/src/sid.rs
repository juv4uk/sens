//! Legacy semantic identity compatibility layer.
//!
//! #1344 / #1386: `Sid8` is a backward-compatible alias for [`Sens8`].
//! The canonical term and primary implementation live in [`crate::sens`].

pub use crate::sens::Sens8;

#[allow(deprecated)]
pub use Sens8 as Sid8;

/// Legacy constructor macro for eight-bit function identity.
///
/// Forwards directly to [`sens!`].
#[macro_export]
macro_rules! sid {
    ($($token:tt)*) => {
        $crate::sens!($($token)*)
    };
}
