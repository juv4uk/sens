//! Direct physical T5 execution. The byte stream already carries exact
//! domain widths; its meaning is owned by the current SENS evaluator.
//!
//! No visible-text source, host Lisp alias, invented resident, or native CPU
//! machine-code claim is constructed by this adapter.

use crate::{
    decode_ternary_words, eval_lowered_expressions, lower_program,
    ternary_transport::parse_t5_domain_words, EvalResult, Expr,
    LanguageError, Session, TernaryTransportError,
};

/// Transport and language failures have distinct, fail-closed provenance.
#[derive(Debug)]
pub enum T5ExecutionError {
    Transport(TernaryTransportError),
    Language(LanguageError),
}

/// Canonically validated physical T5 program, stored as the current lowered AST.
///
/// Decode+parse+the existing interpreter lowering happens once. Repeated
/// evaluation reuses those exact immutable lowered forms,
/// but every evaluation still consults the current interpreter/Session.
/// This is NOT compiled machine code and grants no additional capabilities.
pub struct PhysicalT5Program {
    forms: Vec<Expr>,
}

impl PhysicalT5Program {
    /// Physical bytes -> exact D1-D9 words -> ratified D2 forms, without
    /// creating any text or parsing human identifier surfaces.
    pub fn decode(physical: &[u8]) -> Result<Self, T5ExecutionError> {
        let words = decode_ternary_words(physical).map_err(T5ExecutionError::Transport)?;
        let parsed = parse_t5_domain_words(&words).map_err(T5ExecutionError::Language)?;
        let forms = lower_program(&parsed);
        Ok(Self { forms })
    }

    /// Number of top-level D2 forms; no assumption of a single expression.
    pub fn form_count(&self) -> usize {
        self.forms.len()
    }

    /// Execute decoded forms in an explicitly supplied interpreter session.
    ///
    /// The program does not retain a mutable runtime between calls. Bootstrap,
    /// host capabilities, and session reuse remain the caller's decision.
    pub fn execute(&self, session: &mut Session) -> Result<EvalResult, LanguageError> {
        eval_lowered_expressions(&self.forms, session)
    }
}

/// One-shot version of the same source-free program path.
///
/// Keep this wrapper to preserve the stable public API and ensure it shares
/// the precise decode/parse/evaluate law with `sens-trit eval`.
pub fn eval_t5_program(
    physical: &[u8],
    session: &mut Session,
) -> Result<EvalResult, T5ExecutionError> {
    let program = PhysicalT5Program::decode(physical)?;
    program.execute(session).map_err(T5ExecutionError::Language)
}
