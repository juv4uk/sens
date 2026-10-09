//! Direct execution of physical .sens bytes, not a human-readable alias.
use crate::{decode_ternary_words, eval_parsed_expressions, ternary_transport::parse_t5_domain_words, EvalResult, LanguageError, Session, TernaryTransportError};

/// Transport and language failures have distinct, fail-closed provenance.
#[derive(Debug)]
pub enum T5ExecutionError {
    Transport(TernaryTransportError),
    Language(LanguageError),
}

/// Run a physical T5 stream as an exact-domain program.
///
/// The five-trit packing carries exact binary D1..D9 source words; it is
/// transport only. Those words are packed as semantic bits and parsed by the
/// ratified D2 reader. No text rendering or SID8/human surface router is used.
pub fn eval_t5_program(
    physical: &[u8],
    session: &mut Session,
) -> Result<EvalResult, T5ExecutionError> {
    let words = decode_ternary_words(physical).map_err(T5ExecutionError::Transport)?;
    let forms = parse_t5_domain_words(&words).map_err(T5ExecutionError::Language)?;
    eval_parsed_expressions(&forms, session).map_err(T5ExecutionError::Language)
}
