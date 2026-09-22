//! Mechanical identity for the four my-lisp core profiles (#1131).
//!
//! This module is deliberately semantics-blind. The Lisp-owned
//! `contracts/core-profile-contract.lisp` states profile roles and authority.
//! Rust transports a profile choice and either loads an admitted implementation
//! or fails with `MechanismUnavailable`.

use crate::{load_core_library, ErrorKind, EvalResult, LanguageError, Session, Span};

/// Opaque execution/compatibility profile identity.
///
/// The numeric representation is transport metadata only; it is not a semantic
/// ID and must never be mixed with `Sid8`.
#[repr(u8)]
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum CoreProfile {
    Core1 = 1,
    Core2 = 2,
    Core3 = 3,
    Core4 = 4,
}

impl CoreProfile {
    pub const ALL: [Self; 4] = [Self::Core1, Self::Core2, Self::Core3, Self::Core4];

    pub const fn number(self) -> u8 {
        self as u8
    }

    pub const fn planned_source_path(self) -> &'static str {
        match self {
            Self::Core1 => "lib/core1.lisp",
            Self::Core2 => "lib/core2.lisp",
            Self::Core3 => "lib/core3.lisp",
            Self::Core4 => "lib/core4.lisp",
        }
    }
}

/// Load one explicit core profile.
///
/// During the migration introduced by #1131, the existing `lib/core.lisp`
/// remains the admitted implementation of Core 4. Core 1/2/3 deliberately
/// fail closed until their Lisp-owned sources are admitted; the host must not
/// synthesize compatibility semantics for them.
pub fn load_core_profile(
    session: &mut Session,
    profile: CoreProfile,
) -> Result<EvalResult, LanguageError> {
    match profile {
        CoreProfile::Core4 => load_core_library(session),
        CoreProfile::Core1 | CoreProfile::Core2 | CoreProfile::Core3 => {
            Err(LanguageError::new(
                ErrorKind::MechanismUnavailable,
                format!(
                    "core profile {} is declared but its Lisp implementation is not admitted yet ({})",
                    profile.number(),
                    profile.planned_source_path()
                ),
                Span { start: 0, end: 0 },
            ))
        }
    }
}
