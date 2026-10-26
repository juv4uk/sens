//! Test-only composition of the physical Zig T5M transport and SENS exact-word admission.
//! Production callers use the same public Zig transport directly.

use sens::{EvalResult, LanguageError, PhysicalT5Program, Session};
use sens_cli::zig_transport;

#[derive(Debug)]
pub enum ReferenceT5mError {
    Transport(String),
    Language(LanguageError),
}

impl std::fmt::Display for ReferenceT5mError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Transport(error) => write!(formatter, "Zig T5M transport: {error}"),
            Self::Language(error) => write!(formatter, "SENS exact-word admission: {error:?}"),
        }
    }
}

pub fn admit_reference_t5m(physical: &[u8]) -> Result<PhysicalT5Program, ReferenceT5mError> {
    let words = zig_transport::decode_t5m_words(physical).map_err(ReferenceT5mError::Transport)?;
    PhysicalT5Program::from_exact_words(&words).map_err(ReferenceT5mError::Language)
}

pub fn eval_reference_t5m(
    physical: &[u8],
    session: &mut Session,
) -> Result<EvalResult, ReferenceT5mError> {
    admit_reference_t5m(physical)?
        .execute(session)
        .map_err(ReferenceT5mError::Language)
}
