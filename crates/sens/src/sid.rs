//! Застарілі назви коробки Sens8 — лише для зовнішніх споживачів (juv4uk/cml).
//!
//! Власник, 2026-09-26: єдина назва 1-байтової коробки функцій — `Sens8`
//! (макрос `sens!`). Код `sens` старих назв не використовує; `Sid8` і `sid!`
//! лишаються позначеними `#[deprecated]`, доки `cml` не перейде на `Sens8`.

use crate::sens::Sens8;

#[deprecated(note = "назва коробки — Sens8 (sens!); Sid8 лишено лише для cml")]
pub type Sid8 = Sens8;

/// Застарілий конструктор; використовуйте [`sens!`].
#[deprecated(note = "використовуйте sens!")]
#[macro_export]
macro_rules! sid {
    ($($token:tt)*) => {
        $crate::sens!($($token)*)
    };
}
