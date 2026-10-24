//! Виконавці механізмів, підключених точним доменним диспетчером.
//! Identity та допуск до виклику визначає `canon`, не назви цього модуля.

use crate::environment::Environment;
use crate::eval::special_forms::{
    string_first_values, string_rest_values, string_to_codepoint_values,
};
use crate::{Span, Value};

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

/// Найменша ратифікована знакова ширина D24/D48/D96/D192, що вміщає value.
/// Потрібен ще один біт під знак, тому межа — magnitude_bits + 1.
fn smallest_signed_numeric_width(value: u128) -> Option<usize> {
    let magnitude_bits = (128 - value.leading_zeros()) as usize;
    [24usize, 48, 96, 192]
        .into_iter()
        .find(|width| magnitude_bits + 1 <= *width)
}

/// Точне D24+ значення з невід'ємного цілого (біти MSB-first, як у canon.rs:268).
/// None — значення не вміщається навіть у найширшу ратифіковану D192.
fn exact_domain_from_u128(value: u128) -> Option<Value> {
    let width = smallest_signed_numeric_width(value)?;
    let bits: Vec<u8> = (0..width)
        .rev()
        .map(|shift| if shift >= 128 { 0 } else { ((value >> shift) & 1) as u8 })
        .collect();
    crate::BinaryNumber::from_numeric_domain_bits(width, &bits).map(Value::BinaryNumber)
}

/// Виконавець точного D10-механізму монотонного годинника.
///
/// Першопричина: сигнатура обіцяє «точне ціле» (function_signatures_generated.rs),
/// але механізм повертав `exact_value(..)` — а `exact_value` сам себе документує
/// як «Legacy data/presentation bridge, NOT a mathematical operand admission».
/// Тож `(число? (монотонний-нс))` було ХИБНЕ, і арифметика ВІДХИЛЯЛА власний
/// годинник. Тепер повертається справжнє точнодоменне значення найменшої
/// знакової ширини, що вміщає лічильник.
pub(super) fn monotonic_nanoseconds(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    exact_args(args, 0, span)?;
    static START: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    let elapsed = START.get_or_init(std::time::Instant::now).elapsed();
    exact_domain_from_u128(elapsed.as_nanos()).ok_or_else(|| {
        crate::LanguageError::new(
            crate::ErrorKind::NumericOverflow,
            "monotonic nanosecond counter exceeds the widest exact D192 domain",
            span,
        )
    })
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mechanism_arity_keeps_kind_and_source_span() {
        let span = Span { start: 12, end: 34 };
        for (expected, supplied) in [(0, 1), (1, 0), (1, 2), (2, 1), (3, 4)] {
            let args = vec![Value::Nil; supplied];
            let error = exact_args(&args, expected, span)
                .expect_err("невідповідність арності має завершитися помилкою");
            assert_eq!(error.kind, crate::ErrorKind::Arity);
            assert_eq!(error.span, span);
            assert!(error.message.contains(&format!("очікується {expected}")));
            assert!(error.message.contains(&format!("отримано {supplied}")));
        }
        for expected in 0..=3 {
            exact_args(&vec![Value::Nil; expected], expected, span)
                .expect("точна арність приймається");
        }
    }

    #[test]
    fn string_empty_returns_an_exact_predicate() {
        let environment = Environment::root();
        let value = Value::String(std::rc::Rc::from(""));
        let result = string_empty(&[value], &environment, Span::default()).expect("empty string");
        assert_eq!(result.as_predicate_bit(), Some(true));
        assert_eq!(
            string_empty(&[], &environment, Span::default())
                .expect_err("missing argument is rejected")
                .kind,
            crate::ErrorKind::Arity
        );
    }
}

#[cfg(test)]
mod exact_producer_witness {
    use super::*;
    use crate::domain_numeric;

    /// Першопричина: сигнатура обіцяє «точне ціле», а механізм повертав
    /// legacy-міст (`Value::Number`). Свідок: годинник мусить бути
    /// точнодоменним значенням — тобто `(число? (монотонний-нс))` істинне
    /// і арифметика його приймає.
    #[test]
    fn monotonic_clock_satisfies_d5_numberp() {
        let value = monotonic_nanoseconds(&[], &Environment::root(), Span::default())
            .expect("clock value");
        assert!(
            domain_numeric::is_domain_value(&value),
            "monotonic clock must be an exact D24+ value, not a legacy host Number"
        );
        assert!(
            !matches!(value, Value::Number(..) | Value::Rational(..)),
            "monotonic clock must not return a legacy Number/Rational"
        );
    }

    #[test]
    fn smallest_signed_width_is_chosen_by_magnitude() {
        assert_eq!(smallest_signed_numeric_width(0), Some(24));
        assert_eq!(smallest_signed_numeric_width((1u128 << 22) - 1), Some(24));
        assert_eq!(smallest_signed_numeric_width(1u128 << 23), Some(48));
        assert_eq!(smallest_signed_numeric_width(1u128 << 100), Some(192));
        assert_eq!(smallest_signed_numeric_width(u128::MAX), None);
    }

    #[test]
    fn small_counter_becomes_exact_d24() {
        let value = exact_domain_from_u128(5).expect("5 fits D24");
        assert_eq!(domain_numeric::numeric_value_domain_width(&value), Some(24));
    }
}
