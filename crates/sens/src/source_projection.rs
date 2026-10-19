//! Projection of human-facing Ukrainian decimal integers into exact SENS D24+ values.
//!
//! The source spelling supplies the digits; it is not itself a domain identity.
//! This boundary is deliberately explicit and shared by embedders. It never
//! promotes D1-D10 domain words, host numbers, or fractions into arithmetic.
//! Fractions remain expressible with the admitted Ukrainian `частка` operation.
//!
//! The current source adapter accepts values representable as i128 and fails
//! with a named NumericOverflow beyond that range. No float round-trip occurs.

use crate::syntax::{Expr, ExprKind, Span};
use crate::{BinaryNumber, ErrorKind, LanguageError};
use std::rc::Rc;

/// Project every integer literal written in a human Ukrainian SENS source
/// expression to its exact signed D24/D48/D96/D192 numeric-domain word.
///
/// Call this after `sens::parse` and before `eval_parsed_expressions`.
/// Spans refer to the original source, so diagnostics retain their coordinates.
/// The owning source surface selects when this conversion is applicable.
pub fn project_ukr_decimal_integer_literals(
    expressions: &[Expr],
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    expressions
        .iter()
        .map(|expr| project_expr(expr, source))
        .collect()
}

fn integer_lexeme<'a>(expr: &Expr, source: &'a str) -> Option<&'a str> {
    if !matches!(expr.kind, ExprKind::Number(_, _)) {
        return None;
    }
    let token = source.get(expr.span.start..expr.span.end)?;
    let digits = token
        .strip_prefix('-')
        .or_else(|| token.strip_prefix('+'))
        .unwrap_or(token);
    (!digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit()))
        .then_some(token)
}

fn numeric_domain_width(value: i128) -> usize {
    for width in [24usize, 48, 96] {
        let bound = 1i128 << (width - 1);
        if value >= -bound && value < bound {
            return width;
        }
    }
    192
}

fn project_integer(token: &str, span: Span) -> Result<Expr, LanguageError> {
    let value: i128 = token.parse().map_err(|_| {
        LanguageError::new(
            ErrorKind::NumericOverflow,
            format!("Ukrainian decimal integer exceeds the exact source range: {token}"),
            span,
        )
    })?;
    let width = numeric_domain_width(value);
    // Preserve sign using the ratified D24+ two's-complement integer law.
    // For D192, sign extension above i128 does not shift a host integer by
    // 128 or more; each emitted bit is still part of the exact-width word.
    let bits: Vec<u8> = (0..width)
        .rev()
        .map(|position| {
            if position >= 128 {
                u8::from(value.is_negative())
            } else {
                ((value >> position) & 1) as u8
            }
        })
        .collect();
    let number = BinaryNumber::from_numeric_domain_bits(width, &bits).ok_or_else(|| {
        LanguageError::new(
            ErrorKind::NumericOverflow,
            "could not construct exact D24+ source integer",
            span,
        )
    })?;
    Ok(Expr {
        kind: ExprKind::BinaryNumber(number),
        span,
    })
}

fn project_expr(expr: &Expr, source: &str) -> Result<Expr, LanguageError> {
    if let Some(token) = integer_lexeme(expr, source) {
        return project_integer(token, expr.span);
    }

    let kind = match &expr.kind {
        ExprKind::List(items) => ExprKind::List(
            items
                .iter()
                .map(|item| project_expr(item, source))
                .collect::<Result<Vec<_>, _>>()?
                .into(),
        ),
        ExprKind::Pair(car, cdr) => ExprKind::Pair(
            Rc::new(project_expr(car, source)?),
            Rc::new(project_expr(cdr, source)?),
        ),
        _ => expr.kind.clone(),
    };
    Ok(Expr {
        kind,
        span: expr.span,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn projected_numbers(source: &str) -> Vec<BinaryNumber> {
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("all small integer literals fit their exact domain");
        let [Expr {
            kind: ExprKind::List(items),
            ..
        }] = projected.as_slice()
        else {
            panic!("test source should be one list form");
        };
        items
            .iter()
            .filter_map(|expr| match &expr.kind {
                ExprKind::BinaryNumber(number) => Some(number.clone()),
                _ => None,
            })
            .collect()
    }

    #[test]
    fn decimal_integer_literals_keep_exact_domain_width_and_signed_value() {
        let values = projected_numbers("(приклад 1 -8388608 8388607 8388608)");
        assert_eq!(values.len(), 4);
        assert_eq!(values[0].numeric_domain_width(), Some(24));
        assert_eq!(values[1].numeric_domain_width(), Some(24));
        assert_eq!(values[2].numeric_domain_width(), Some(24));
        assert_eq!(values[3].numeric_domain_width(), Some(48));
        assert_eq!(values[0].to_decimal_string(), "1");
        assert_eq!(values[1].to_decimal_string(), "-8388608");
        assert_eq!(values[2].to_decimal_string(), "8388607");
        assert_eq!(values[3].to_decimal_string(), "8388608");
    }

    #[test]
    fn integer_projection_recurses_into_nested_and_quoted_source_data() {
        let source = "(як-є (сполучити 2 (сполучити -3 (як-є ()))))";
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("integer data is exactly projected");
        fn count_words(expr: &Expr) -> usize {
            match &expr.kind {
                ExprKind::BinaryNumber(_) => 1,
                ExprKind::List(items) => items.iter().map(count_words).sum(),
                ExprKind::Pair(car, cdr) => count_words(car) + count_words(cdr),
                _ => 0,
            }
        }
        assert_eq!(projected.iter().map(count_words).sum::<usize>(), 2);
    }

    #[test]
    fn integer_projection_fails_named_beyond_the_supported_exact_source_range() {
        let source = "(додати 170141183460469231731687303715884105728 1)";
        let parsed = crate::parse(source).expect("reader preserves large integer atom");
        let error = project_ukr_decimal_integer_literals(&parsed, source)
            .expect_err("overflow cannot silently remain an unqualified host number");
        assert_eq!(error.kind, ErrorKind::NumericOverflow);
    }

    #[test]
    fn fractional_and_symbol_tokens_are_not_silently_reinterpreted_as_integers() {
        let source = "(приклад радіо 0.25)";
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("noninteger source tokens are not integer-promoted");
        let ExprKind::List(items) = &projected[0].kind else {
            panic!("expected list")
        };
        assert!(matches!(items[1].kind, ExprKind::Symbol(_)));
        assert!(!matches!(items[2].kind, ExprKind::BinaryNumber(_)));
    }
}
