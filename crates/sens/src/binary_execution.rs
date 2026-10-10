//! Direct execution of physical .sens bytes, not a human-readable alias.
use crate::{
    decode_ternary_words, eval_lowered_expressions, eval_parsed_expressions, lower_program,
    ternary_transport::parse_t5_domain_words, EvalResult, Expr, LanguageError, Session,
    TernaryTransportError,
};

/// Transport and language failures have distinct, fail-closed provenance.
#[derive(Debug)]
pub enum T5ExecutionError {
    Transport(TernaryTransportError),
    Language(LanguageError),
}

/// Immutable executable program derived *only* from validated physical T5.
///
/// Preparation performs the same physical-byte validation, exact-width domain
/// recovery and D2 grammar as `eval_t5_program`, then lowers the AST once.
/// No semantic result or mutable Session is cached. D1 predicate checking,
/// dynamic environment access and every evaluator error still happen at EACH
/// execution. A fresh Session::bare() needs no Core4 bootstrap for ratified
/// primitive D1/D2/D3 programs.
///
/// This is a mechanical predecode substrate, not a separate interpreter,
/// bytecode law, AOT compiler, or authority over domain semantics.
#[derive(Clone, Debug)]
pub struct PreparedT5Program {
    lowered: Vec<Expr>,
}

impl PreparedT5Program {
    /// Execute against the explicitly provided environment, preserving the
    /// exact current evaluator and its fail-closed runtime control rules.
    pub fn execute(&self, session: &mut Session) -> Result<EvalResult, LanguageError> {
        eval_lowered_expressions(&self.lowered, session)
    }

    pub fn form_count(&self) -> usize {
        self.lowered.len()
    }
}

/// Validate + decode physical T5, parse ratified D2, and lower a program once.
///
/// No visible text translation or external width-schedule is involved.
/// Transport errors cannot be skipped by calling the prepared executor.
pub fn prepare_t5_program(physical: &[u8]) -> Result<PreparedT5Program, T5ExecutionError> {
    let words = decode_ternary_words(physical).map_err(T5ExecutionError::Transport)?;
    let forms = parse_t5_domain_words(&words).map_err(T5ExecutionError::Language)?;
    Ok(PreparedT5Program {
        lowered: lower_program(&forms),
    })
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
