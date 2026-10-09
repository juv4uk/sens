//! Execute physical SENS .sens/T5 bytes as the primary exact-domain program.
//!
//! There is no source-string parser or historical SID8 name router on this
//! entry point. Physical T5 is merely word-boundary transport: the domain
//! payload remains binary (D1..D9), and D2 owns its structural grammar.

use crate::{
    decode_ternary_words, eval_parsed_expressions, parse_canonical_words, EvalResult,
    LanguageError, Session, TernaryTransportError,
};

/// Fail-closed distinction between corrupt/noncanonical physical transport
/// and a parsed binary program rejected by language-owned mechanisms.
#[derive(Debug)]
pub enum T5ExecutionError {
    Transport(TernaryTransportError),
    Language(LanguageError),
}

/// Run physical `.sens` bytes through the canonical exact-domain evaluator.
///
/// Decodes T5, validates D2 structure over typed words, then lowers and
/// evaluates exact domain identities. No Unicode, English, Sanskrit, or
/// historical SID8 spelling is reconstructed along this executable path.
///
/// Use a fresh `Session::default()` for self-contained binary programs.
/// Additional language-owned definitions may be explicitly loaded by a caller.
pub fn eval_t5_program(
    physical: &[u8],
    session: &mut Session,
) -> Result<EvalResult, T5ExecutionError> {
    let words = decode_ternary_words(physical).map_err(T5ExecutionError::Transport)?;
    let expressions = parse_canonical_words(&words).map_err(T5ExecutionError::Language)?;
    eval_parsed_expressions(&expressions, session).map_err(T5ExecutionError::Language)
}
