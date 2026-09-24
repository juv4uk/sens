//! Exact eight-bit function sense (СЕНС).
//!
//! #1344: Renames the technical acronym `SID` to the ontological term `sens` (СЕНС).
//! In `my-lisp`, exactly 256 functions exist in the `00000000..11111111` space.
//! Each eight-bit value is the direct `sens` (meaning, sense, вектор, сутність)
//! of the function itself, not an arbitrary database identifier.

pub use crate::sid::Sid8 as Sens8;
pub use Sens8 as Sens;

/// Canonical constructor macro for eight-bit function sense (СЕНС).
///
/// ```
/// let s = my_lisp::sens!(00000011);
/// assert_eq!(s, my_lisp::sid!(00000011));
/// ```
#[macro_export]
macro_rules! sens {
    ($($token:tt)*) => {
        $crate::sid!($($token)*)
    };
}
