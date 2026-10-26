
use sens_cli::zig_transport;//! Test-only composition of the reference Rust transport and SENS exact-word
//! reader. Production callers must restore physical words through Zig.

use sens::{BinarySourceWord, EvalResult, LanguageError, PhysicalT5Program, Session,
    TernaryTransportError,
};

#[derive(Debug)]
pub enum ReferenceT5mError {
    Transport(TernaryTransportError),
    Language(LanguageError),
}

impl std::fmt::Display for ReferenceT5mError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Transport(error) => write!(formatter, "T5M reference transport: {error:?}"),
            Self::Language(error) => write!(formatter, "SENS exact-word admission: {error:?}"),
        }
    }
}

pub fn admit_reference_t5m(physical: &[u8]) -> Result<PhysicalT5Program, ReferenceT5mError> {
    let words = decode_ternary_words(physical).map_err(ReferenceT5mError::Transport)?;
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

// Обгортки над чинним Zig T5M: staged-out ternary виведено (f5a5b213).
fn decode_ternary_words(bytes: &[u8]) -> Result<Vec<BinarySourceWord>, String> {
    zig_transport::decode_t5m_words(bytes)
}
