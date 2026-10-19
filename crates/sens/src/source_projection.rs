//! Projection of human-facing Ukrainian decimal integers into exact SENS D24+ values.
//!
//! The source spelling supplies the digits; it is not itself a domain identity.
//! This boundary is shared by embedders. It never promotes D1-D10 words or
//! host numbers into arithmetic. Fractions remain expressible with the admitted
//! Ukrainian `частка` operation.
//!
//! Integers are source-qualified to the smallest signed D24/D48/D96/D192 word
//! that contains their value. Within one connected D5 numeric expression tree,
//! all source integer leaves receive the same widest required domain. This
//! prevents an expression such as `(додати 8388608 1)` from mixing D48 and D24.
//! Values outside i128 fail by a named NumericOverflow, never through float.

use crate::syntax::{Expr, ExprKind, Span};
use crate::{BinaryNumber, ErrorKind, LanguageError};
use std::rc::Rc;

/// Project integer literals in Ukrainian source before evaluation.
///
/// Numeric literals in one connected D5 call tree share the widest required
/// numeric domain; independent values retain their smallest exact domain.
/// Source spans are preserved for diagnostics. The owning surface chooses when
/// this conversion is applicable.
pub fn project_ukr_decimal_integer_literals(
    expressions: &[Expr],
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    expressions
        .iter()
        .map(|expr| project_expr(expr, source, None))
        .collect()
}

fn integer_lexeme<'a>(expr: &Expr, source: &'a str) -> Option<&'a str> {
    if matches!(
        &expr.kind,
        ExprKind::DomainCall(..)
            | ExprKind::Call(..)
            | ExprKind::List(..)
            | ExprKind::Pair(..)
    ) {
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

fn integer_width(token: &str, span: Span) -> Result<usize, LanguageError> {
    let value: i128 = token.parse().map_err(|_| {
        LanguageError::new(
            ErrorKind::NumericOverflow,
            format!("Ukrainian decimal integer exceeds the exact source range: {token}"),
            span,
        )
    })?;
    Ok(numeric_domain_width(value))
}

fn project_integer(token: &str, span: Span, width: usize) -> Result<Expr, LanguageError> {
    let value: i128 = token.parse().map_err(|_| {
        LanguageError::new(
            ErrorKind::NumericOverflow,
            format!("Ukrainian decimal integer exceeds the exact source range: {token}"),
            span,
        )
    })?;
    let width = width.max(numeric_domain_width(value));
    // Two's complement, including sign-extension for D192 values. Never shift
    // a host integer by 128 or more; those upper bits are explicit sign bits.
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

/// Human source remains symbol-headed at reader level. Consult the canonical
/// registry instead of maintaining a local list of D5 function names.
fn is_d5_call(expr: &Expr) -> bool {
    let ExprKind::List(items) = &expr.kind else {
        return false;
    };
    let Some(Expr { kind: ExprKind::Symbol(name), .. }) = items.first() else {
        return false;
    };
    crate::semantic_registry_export::admitted_core_domain_for_surface(name)
        .is_some_and(|identity| identity.width() == 5)
}

fn required_width_in_math_tree(
    expr: &Expr,
    source: &str,
    depth: usize,
) -> Result<Option<usize>, LanguageError> {
    if depth > 768 {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "Ukrainian numeric source exceeds nesting limit",
            expr.span,
        ));
    }
    if let Some(token) = integer_lexeme(expr, source) {
        return integer_width(token, expr.span).map(Some);
    }
    if !is_d5_call(expr) {
        return Ok(None);
    }
    let ExprKind::List(items) = &expr.kind else {
        unreachable!("is_d5_call requires a list")
    };
    let mut width = None;
    for argument in items.iter().skip(1) {
        if let Some(required) = required_width_in_math_tree(argument, source, depth + 1)? {
            width = Some(width.map_or(required, |current: usize| current.max(required)));
        }
    }
    Ok(width)
}

fn project_expr(
    expr: &Expr,
    source: &str,
    inherited_math_width: Option<usize>,
) -> Result<Expr, LanguageError> {
    if let Some(token) = integer_lexeme(expr, source) {
        let width = match inherited_math_width {
            Some(width) => width.max(integer_width(token, expr.span)?),
            None => integer_width(token, expr.span)?,
        };
        return project_integer(token, expr.span, width);
    }

    let kind = match &expr.kind {
        ExprKind::List(items) if is_d5_call(expr) => {
            let required = required_width_in_math_tree(expr, source, 0)?.unwrap_or(24);
            let width = inherited_math_width.map_or(required, |outer| outer.max(required));
            ExprKind::List(
                items
                    .iter()
                    .enumerate()
                    .map(|(index, item)| {
                        if index == 0 {
                            Ok(item.clone())
                        } else {
                            project_expr(item, source, Some(width))
                        }
                    })
                    .collect::<Result<Vec<_>, LanguageError>>()?
                    .into(),
            )
        }
        ExprKind::List(items) => ExprKind::List(
            items
                .iter()
                // A data/syntax form starts a fresh numeric context. An actual
                // D5 call discovers its own required domain when visited.
                .map(|item| project_expr(item, source, None))
                .collect::<Result<Vec<_>, _>>()?
                .into(),
        ),
        ExprKind::Pair(car, cdr) => ExprKind::Pair(
            Rc::new(project_expr(car, source, None)?),
            Rc::new(project_expr(cdr, source, None)?),
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
    fn one_math_tree_uses_one_exact_width_for_all_decimal_leaves() {
        let source = "(додати 8388608 1)";
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("both operands receive one common exact domain");
        let [Expr { kind: ExprKind::List(items), .. }] = projected.as_slice() else {
            panic!("expected one list form");
        };
        let widths: Vec<_> = items.iter().skip(1).map(|expr| match &expr.kind {
            ExprKind::BinaryNumber(number) => number.numeric_domain_width(),
            _ => None,
        }).collect();
        assert_eq!(widths, vec![Some(48), Some(48)]);
    }

    #[test]
    fn nested_math_tree_propagates_the_required_width_without_coercing_values() {
        let source = "(додати 1 (помножити 8388608 2))";
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("one math tree has a shared source-selected domain");
        let [Expr { kind: ExprKind::List(items), .. }] = projected.as_slice() else {
            panic!("expected one list form");
        };
        let ExprKind::BinaryNumber(left) = &items[1].kind else {
            panic!("expected outer integer")
        };
        let ExprKind::List(nested) = &items[2].kind else {
            panic!("expected nested multiply")
        };
        assert_eq!(left.numeric_domain_width(), Some(48));
        let widths: Vec<_> = nested.iter().skip(1).map(|expr| match &expr.kind {
            ExprKind::BinaryNumber(number) => number.numeric_domain_width(),
            _ => None,
        }).collect();
        assert_eq!(widths, vec![Some(48), Some(48)]);
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
    fn projected_ukr_quotient_reaches_the_exact_d5_resident() {
        // This reproduces the IDE's source -> exact-domain AST -> evaluator
        // boundary. The registered D5:10111 operation must return exact RATIO,
        // not fall through to the Lisp-owned integer-quotient helper.
        let source = "(частка 1 3)";
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("source decimal integers become D24 words");
        let lowered = crate::lower_program(&projected);
        assert!(matches!(
            &lowered[0].kind,
            ExprKind::DomainCall(identity, _)
                if identity.width() == 5 && identity.packed_bits() == 0b10111
        ), "D5:10111 must be the immutable call head, not a rebindable Lisp name");

        let mut session = crate::Session::default();
        crate::load_core_library(&mut session).expect("Core library loads");
        let result = crate::eval_parsed_expressions(&projected, &mut session)
            .expect("exact D5 quotient evaluates");
        let crate::Value::NumericComposition(composition) = &result.value else {
            panic!("D5:10111 must produce an exact RATIO composition");
        };
        let (_, numerator, denominator) = composition.as_parts();
        assert_eq!(numerator.to_unsigned_decimal_string(), "1");
        assert_eq!(
            denominator.expect("nonintegral quotient has denominator").to_unsigned_decimal_string(),
            "3"
        );
    }

    #[test]
    fn projected_nested_ukr_quotients_remain_exact_under_addition() {
        let source = "(додати (частка 1 3) (частка 1 3))";
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("source decimal integers become D24 words");
        let mut session = crate::Session::default();
        crate::load_core_library(&mut session).expect("Core library loads");
        let result = crate::eval_parsed_expressions(&projected, &mut session)
            .expect("exact D5 nested arithmetic evaluates");
        let crate::Value::NumericComposition(composition) = &result.value else {
            panic!("D5 arithmetic must produce an exact RATIO composition");
        };
        let (_, numerator, denominator) = composition.as_parts();
        assert_eq!(numerator.to_unsigned_decimal_string(), "2");
        assert_eq!(
            denominator.expect("nonintegral sum has denominator").to_unsigned_decimal_string(),
            "3"
        );
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
        assert!(matches!(&items[1].kind, ExprKind::Symbol(_)));
        assert!(!matches!(&items[2].kind, ExprKind::BinaryNumber(_)));
    }
}
