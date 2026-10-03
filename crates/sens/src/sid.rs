//! Historical SID spellings for the legacy exact-eight compatibility carrier.
//!
//! `Sid8` / `sid!` predate the domain-qualified ontology and remain only so
//! old external consumers can migrate without an ABI/source cliff. They are not
//! aliases for canonical semantic identity. New semantic code must preserve the
//! exact SENS domain; even `Sens8` itself is now compatibility/transport only.

use crate::sens::Sens8;

#[deprecated(note = "Sid8 is historical compatibility only; canonical semantics use exact domain identity")]
pub type Sid8 = Sens8;

/// Historical exact-eight constructor kept only for compatibility.
///
/// `sens!` is the corresponding legacy exact-eight spelling; neither macro
/// infers a canonical semantic domain.
#[deprecated(note = "sid! is historical compatibility only; preserve exact domain identity in new semantic code")]
#[macro_export]
macro_rules! sid {
    ($($token:tt)*) => {
        $crate::sens!($($token)*)
    };
}
