//! Pure two-phase evaluation API for sens-host.
//!
//! # Motivation (#1766)
//!
//! The original host capability functions (`evaluate_read_dir`, etc.) each
//! call `eval_expr` on raw `Expr` arguments *inside* the host function body.
//! That means the evaluator re-enters itself through the host boundary — the
//! host is not a pure mechanism.
//!
//! The correct direction: **the evaluator lowers and evaluates arguments
//! before invoking a host capability**; the host function receives concrete
//! `Value`s and performs the OS operation. This module exposes the two-phase
//! shape at the crate API level:
//!
//! ```text
//! parse_and_lower(src)              →  Vec<Expr>     (parsed + lowered)
//! eval_lowered(exprs, &mut session) →  EvalResult    (pure evaluation)
//! ```
//!
//! Callers currently using `sens::eval_program` (the full round-trip) can
//! migrate to `parse_and_lower` + `eval_lowered` to separate parse errors
//! from evaluation errors and to run the two phases independently.

use sens::{parse, lower_program, eval_lowered_expressions, Expr, LanguageError, EvalResult, Session};

/// Parse a source string and lower it to a list of expressions ready for
/// evaluation.
///
/// `lower_program` applies macro-expansion and any compile-time rewriting
/// defined by the language core. The result is a `Vec<Expr>` that can be
/// passed directly to [`eval_lowered`].
///
/// Errors come from the parser; lowering is infallible in the current
/// implementation.
pub fn parse_and_lower(src: &str) -> Result<Vec<Expr>, LanguageError> {
    let parsed = parse(src)?;
    let lowered = lower_program(&parsed);
    Ok(lowered)
}

/// Evaluate a list of already-lowered expressions against a mutable `Session`.
///
/// Returns the `EvalResult` of the last expression (value + any output), or a
/// `LanguageError` if evaluation fails.
///
/// This is the counterpart to [`parse_and_lower`]: together they expose the
/// parse and evaluation phases without coupling them, keeping the host as a
/// pure mechanism boundary.
pub fn eval_lowered(exprs: Vec<Expr>, session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_lowered_expressions(&exprs, session)
}
