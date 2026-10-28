//! Виконавці механізмів, підключених точним доменним диспетчером.
//! Identity та допуск до виклику визначає `canon`, не назви цього модуля.

use crate::environment::Environment;
use crate::eval::arithmetic::exact_value;
use crate::eval::special_forms::{
    string_first_values, string_rest_values, string_to_codepoint_values,
};
use crate::{Rational, Span, Value};

fn exact_args(args: &[Value], expected: usize, span: Span) -> Result<(), crate::LanguageError> {
    if args.len() != expected {
        return Err(crate::LanguageError::new(
            crate::ErrorKind::Arity,
            format!(
                "невірна кількість аргументів: очікується {expected}, отримано {}",
                args.len()
            ),
            span,
        ));
    }
    Ok(())
}

/// Виконавець точного D10-механізму монотонного годинника.
pub(super) fn monotonic_nanoseconds(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    exact_args(args, 0, span)?;
    static START: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    let elapsed = START.get_or_init(std::time::Instant::now).elapsed();
    Ok(exact_value(Rational::integer(elapsed.as_nanos() as i64)))
}

/// Snapshot the current lexical environment as a Lisp list of name/value pairs.
/// The Environment owns scope and shadowing; this function only exposes its
/// already-resolved visible bindings as ordinary SENS data.
pub(super) fn environment_reflection(
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    exact_args(args, 0, span)?;
    Ok(Value::list(environment.snapshot().into_iter().map(
        |(name, value)| Value::list([Value::Symbol(name), value]),
    )))
}

/// Конвертує рядкове представлення символу в точне числове значення.
pub(super) fn string_to_codepoint(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    string_to_codepoint_values(args, span)
}

pub(super) fn string_empty(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    exact_args(args, 1, span)?;
    string_empty_answer(&args[0], span)
}

pub(super) fn string_rest(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    string_rest_values(args, span)
}

pub(super) fn string_prefix(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    exact_args(args, 2, span)?;
    string_prefix_answer(&args[0], &args[1], span)
}

pub(super) fn string_first(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    string_first_values(args, span)
}

fn string_first_or_error(value: &Value, span: Span) -> Result<Value, crate::LanguageError> {
    string_first_values(std::slice::from_ref(value), span)
}

fn is_empty_string(value: &Value) -> bool {
    matches!(value, Value::String(text) if text.is_empty())
}

fn string_empty_answer(value: &Value, span: Span) -> Result<Value, crate::LanguageError> {
    super::special_forms::eq_values(value.clone(), Value::String(std::rc::Rc::from("")), span)
}

fn string_prefix_answer(
    prefix: &Value,
    text: &Value,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    match (prefix, text) {
        (Value::String(prefix), Value::String(text)) => {
            Ok(Value::predicate_bit(text.starts_with(prefix.as_ref())))
        }
        _ => {
            if is_empty_string(prefix) {
                return Ok(Value::predicate_bit(true));
            }
            string_empty_answer(prefix, span)?;
            if is_empty_string(text) {
                return Ok(Value::predicate_bit(false));
            }
            string_empty_answer(text, span)?;
            string_first_or_error(prefix, span)?;
            string_first_or_error(text, span)?;
            unreachable!("string-first accepts only strings")
        }
    }
}

