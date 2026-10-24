//! Projection of human-facing Ukrainian decimal integers into exact SENS D12+ values.
//!
//! The source spelling supplies the digits; it is not itself a domain identity.
//! This boundary is shared by embedders. It never promotes D1-D10 words or
//! host numbers into arithmetic. Fractions remain expressible with the admitted
//! Ukrainian `частка` operation.
//!
//! Integers are source-qualified to the smallest signed D12/D24/D48/D96/D192 word
//! that contains their value. Within one connected D5 numeric expression tree,
//! all source integer leaves receive the same widest required domain. This
//! prevents an expression such as `(додати 8388608 1)` from mixing D48 and D24.
//! Values are converted digit-by-digit and fail only beyond signed D192, never through a host integer or float.

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
    project_ukr_decimal_integer_literals_with_minimum_width(expressions, source, 24)
}

/// Project source integers using an explicit numeric-domain floor.
///
/// D12-first execution passes 12; callers which deliberately operate inside an
/// established D24+ Core4 profile pass 24. This is a source-profile choice, not
/// inference from a bit carrier or silent mixed-domain coercion.
pub fn project_ukr_decimal_integer_literals_with_minimum_width(
    expressions: &[Expr],
    source: &str,
    minimum_width: usize,
) -> Result<Vec<Expr>, LanguageError> {
    if !BinaryNumber::is_numeric_domain_width(minimum_width) {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!("unsupported numeric projection floor D{minimum_width}"),
            expressions.first().map_or(
                Span { start: 0, end: source.len() },
                |expr| expr.span,
            ),
        ));
    }
    expressions
        .iter()
        .map(|expr| project_expr(expr, source, None, minimum_width))
        .collect()
}

fn integer_lexeme<'a>(expr: &Expr, source: &'a str) -> Option<&'a str> {
    if matches!(
        &expr.kind,
        ExprKind::DomainCall(..)
            | ExprKind::DomainIdentity(..)
            | ExprKind::Call(..)
            | ExprKind::Sid(..)
            | ExprKind::BinaryNumber(..)
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
    (!digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit())).then_some(token)
}

/// Convert decimal digits to a magnitude bit vector without routing through
/// a host integer type. The source domain, not i128/u64, owns the width.
fn decimal_magnitude_bits(token: &str, span: Span) -> Result<(bool, Vec<u8>), LanguageError> {
    let (negative, digits) = if let Some(rest) = token.strip_prefix('-') {
        (true, rest)
    } else if let Some(rest) = token.strip_prefix('+') {
        (false, rest)
    } else {
        (false, token)
    };
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(LanguageError::new(
            ErrorKind::NumericOverflow,
            format!("invalid Ukrainian decimal integer source token: {token}"),
            span,
        ));
    }

    let mut decimal: Vec<u8> = digits.bytes().map(|byte| byte - b'0').collect();
    while decimal.len() > 1 && decimal[0] == 0 {
        decimal.remove(0);
    }
    let mut reversed_bits = Vec::new();
    while decimal.iter().any(|digit| *digit != 0) {
        let mut carry = 0u8;
        for digit in &mut decimal {
            let value = carry * 10 + *digit;
            *digit = value / 2;
            carry = value % 2;
        }
        reversed_bits.push(carry);
        while decimal.len() > 1 && decimal[0] == 0 {
            decimal.remove(0);
        }
    }
    if reversed_bits.is_empty() {
        reversed_bits.push(0);
    }
    reversed_bits.reverse();
    Ok((negative, reversed_bits))
}

fn magnitude_fits_signed_width(negative: bool, magnitude: &[u8], width: usize) -> bool {
    if magnitude.len() < width {
        return true;
    }
    negative
        && magnitude.len() == width
        && magnitude[0] == 1
        && magnitude[1..].iter().all(|bit| *bit == 0)
}

fn integer_width(token: &str, span: Span) -> Result<usize, LanguageError> {
    let (negative, magnitude) = decimal_magnitude_bits(token, span)?;
    [12usize, 24, 48, 96, 192]
        .into_iter()
        .find(|width| magnitude_fits_signed_width(negative, &magnitude, *width))
        .ok_or_else(|| {
            LanguageError::new(
                ErrorKind::NumericOverflow,
                format!("Ukrainian decimal integer exceeds the exact D192 source range: {token}"),
                span,
            )
        })
}

fn project_integer(
    token: &str,
    span: Span,
    inherited_width: usize,
    minimum_width: usize,
) -> Result<Expr, LanguageError> {
    let (negative, magnitude) = decimal_magnitude_bits(token, span)?;
    let required_width = integer_width(token, span, minimum_width)?;
    let width = inherited_width.max(required_width);
    let mut bits = vec![0u8; width];
    for (index, bit) in magnitude.iter().rev().enumerate() {
        if index >= width {
            return Err(LanguageError::new(
                ErrorKind::NumericOverflow,
                format!("Ukrainian decimal integer exceeds selected D{width} width: {token}"),
                span,
            ));
        }
        bits[width - 1 - index] = *bit;
    }
    if negative {
        // Exact two's complement is constructed in the selected domain width.
        for bit in &mut bits {
            *bit ^= 1;
        }
        for bit in bits.iter_mut().rev() {
            if *bit == 0 {
                *bit = 1;
                break;
            }
            *bit = 0;
        }
    }
    let number = BinaryNumber::from_numeric_domain_bits(width, &bits).ok_or_else(|| {
        LanguageError::new(
            ErrorKind::NumericOverflow,
            format!("could not construct exact D{width} source integer"),
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
    let Some(Expr {
        kind: ExprKind::Symbol(name),
        ..
    }) = items.first()
    else {
        return false;
    };
    crate::semantic_registry_export::admitted_core_domain_for_surface(name)
        .is_some_and(|identity| identity.width() == 5)
}

fn required_width_in_math_tree(
    expr: &Expr,
    source: &str,
    depth: usize,
    minimum_width: usize,
) -> Result<Option<usize>, LanguageError> {
    if depth > 768 {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "Ukrainian numeric source exceeds nesting limit",
            expr.span,
        ));
    }
    if let Some(token) = integer_lexeme(expr, source) {
        return integer_width(token, expr.span, minimum_width).map(Some);
    }
    if !is_d5_call(expr) {
        return Ok(None);
    }
    let ExprKind::List(items) = &expr.kind else {
        unreachable!("is_d5_call requires a list")
    };
    let mut width = None;
    for argument in items.iter().skip(1) {
        if let Some(required) =
            required_width_in_math_tree(argument, source, depth + 1, minimum_width)?
        {
            width = Some(width.map_or(required, |current: usize| current.max(required)));
        }
    }
    Ok(width)
}

fn is_quoted_source_form(expr: &Expr, source: &str) -> bool {
    let ExprKind::List(items) = &expr.kind else {
        // A parser-owned historical call node is opaque as a whole. It must
        // not be deconstructed here to discover numeric operands.
        return matches!(expr.kind, ExprKind::Call(..) | ExprKind::Sid(..));
    };
    let Some(head) = items.first() else {
        return false;
    };
    if matches!(&head.kind, ExprKind::DomainIdentity(identity)
        if identity.width() == 3 && identity.packed_bits() == 0b001)
    {
        return true;
    }
    if matches!(&head.kind, ExprKind::Symbol(name)
        if matches!(name.as_ref(), "як-є" | "quote" | "'"))
    {
        return true;
    }
    source
        .get(head.span.start..head.span.end)
        .is_some_and(|spelling| matches!(spelling, "001" | "'" | "00000001"))
}

fn project_expr(
    expr: &Expr,
    source: &str,
    inherited_math_width: Option<usize>,
    minimum_width: usize,
) -> Result<Expr, LanguageError> {
    // Quoted forms are syntax/data. Their contents may include decimal digits,
    // domain-shaped atoms, or source code; projection must preserve every one.
    if is_quoted_source_form(expr, source) {
        return Ok(expr.clone());
    }
    if let Some(token) = integer_lexeme(expr, source) {
        let width = match inherited_math_width {
            Some(width) => width.max(integer_width(token, expr.span, minimum_width)?),
            None => integer_width(token, expr.span, minimum_width)?,
        };
        return project_integer(token, expr.span, width, minimum_width);
    }

    let kind = match &expr.kind {
        ExprKind::List(items) if is_d5_call(expr) => {
            let required = required_width_in_math_tree(expr, source, 0)?.unwrap_or(12);
            let width = inherited_math_width.map_or(required, |outer| outer.max(required));
            ExprKind::List(
                items
                    .iter()
                    .enumerate()
                    .map(|(index, item)| {
                        if index == 0 {
                            Ok(item.clone())
                        } else {
                            project_expr(item, source, Some(width), minimum_width)
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
                .map(|item| project_expr(item, source, None, minimum_width))
                .collect::<Result<Vec<_>, _>>()?
                .into(),
        ),
        ExprKind::Pair(car, cdr) => ExprKind::Pair(
            Rc::new(project_expr(car, source, None, minimum_width)?),
            Rc::new(project_expr(cdr, source, None, minimum_width)?),
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
    fn decimal_integer_source_uses_exact_signed_d12_edges() {
        for (source, expected) in [
            ("0", "0"),
            ("1", "1"),
            ("-1", "-1"),
            ("2047", "2047"),
            ("-2048", "-2048"),
        ] {
            let parsed = crate::parse(source).expect("D12 boundary parses");
            let projected = project_ukr_decimal_integer_literals(&parsed, source)
                .expect("D12 boundary projects exactly");
            let ExprKind::BinaryNumber(value) = &projected[0].kind else {
                panic!("decimal source must become an exact numeric-domain word");
            };
            assert_eq!(value.numeric_domain_width(), Some(12), "{source}");
            assert_eq!(value.to_decimal_string(), expected, "{source}");
        }

        let source = "2048";
        let parsed = crate::parse(source).expect("first positive overflow parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("positive overflow widens without wrapping");
        let ExprKind::BinaryNumber(value) = &projected[0].kind else {
            panic!("overflow result must remain an exact numeric-domain word");
        };
        assert_eq!(value.numeric_domain_width(), Some(24));
        assert_eq!(value.to_decimal_string(), "2048");
    }

    #[test]
    fn decimal_integer_literals_keep_exact_domain_width_and_signed_value() {
        let values = projected_numbers("(приклад 1 -8388608 8388607 8388608)");
        assert_eq!(values.len(), 4);
        assert_eq!(values[0].numeric_domain_width(), Some(12));
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
        let [Expr {
            kind: ExprKind::List(items),
            ..
        }] = projected.as_slice()
        else {
            panic!("expected one list form");
        };
        let widths: Vec<_> = items
            .iter()
            .skip(1)
            .map(|expr| match &expr.kind {
                ExprKind::BinaryNumber(number) => number.numeric_domain_width(),
                _ => None,
            })
            .collect();
        assert_eq!(widths, vec![Some(48), Some(48)]);
    }

    #[test]
    fn nested_math_tree_propagates_the_required_width_without_coercing_values() {
        let source = "(додати 1 (помножити 8388608 2))";
        let parsed = crate::parse(source).expect("source parses");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("one math tree has a shared source-selected domain");
        let [Expr {
            kind: ExprKind::List(items),
            ..
        }] = projected.as_slice()
        else {
            panic!("expected one list form");
        };
        let ExprKind::BinaryNumber(left) = &items[1].kind else {
            panic!("expected outer integer")
        };
        let ExprKind::List(nested) = &items[2].kind else {
            panic!("expected nested multiply")
        };
        assert_eq!(left.numeric_domain_width(), Some(48));
        let widths: Vec<_> = nested
            .iter()
            .skip(1)
            .map(|expr| match &expr.kind {
                ExprKind::BinaryNumber(number) => number.numeric_domain_width(),
                _ => None,
            })
            .collect();
        assert_eq!(widths, vec![Some(48), Some(48)]);
    }

    #[test]
    fn already_typed_domain_data_is_not_reinterpreted_as_decimal_source() {
        let source = "0011";
        let word = crate::parse_binary_source_words(source)
            .expect("fixture uses the exact-width source-word reader");
        let identity = crate::DomainIdentity::from_source_word(word[0].word);
        let typed = Expr {
            kind: ExprKind::DomainIdentity(identity),
            span: Span {
                start: 0,
                end: source.len(),
            },
        };
        let projected = project_ukr_decimal_integer_literals(&[typed], source)
            .expect("already-typed domain identity remains a domain identity");
        assert!(
            matches!(&projected[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 4 && identity.packed_bits() == 0b0011
            ),
            "domain width and exact bits must survive source projection unchanged"
        );
    }

    #[test]
    fn quoted_source_data_keeps_decimal_atoms_and_nested_code_unchanged() {
        for source in [
            "(як-є (сполучити 2 (сполучити -3 (як-є ()))))",
            "(00000001 (100 x))",
        ] {
            let parsed = crate::parse(source).expect("source parses");
            let projected = project_ukr_decimal_integer_literals(&parsed, source)
                .expect("quoted source data remains opaque");
            assert_eq!(
                projected, parsed,
                "projection must not recurse beneath QUOTE: {source}"
            );
        }
        let source = "(як-є (сполучити 2 (сполучити -3 (як-є ()))))";
        let parsed = crate::parse(source).expect("source parses");
        let ExprKind::List(outer) = &parsed[0].kind else {
            panic!("outer QUOTE");
        };
        let ExprKind::List(data) = &outer[1].kind else {
            panic!("quoted list data");
        };
        assert!(matches!(&data[1].kind, ExprKind::Number(value, _) if *value == 2.0));
    }

    #[test]
    fn source_integers_above_i128_use_exact_d192_words_without_float_round_trip() {
        let source = "(додати 170141183460469231731687303715884105728 1)";
        let parsed = crate::parse(source).expect("reader preserves a large decimal atom");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("2^127 is a valid signed D192 source integer");
        let ExprKind::List(items) = &projected[0].kind else {
            panic!("expected one D5 arithmetic form")
        };
        let ExprKind::BinaryNumber(value) = &items[1].kind else {
            panic!("large decimal operand must become an exact binary-domain word")
        };
        assert_eq!(value.numeric_domain_width(), Some(192));
        assert_eq!(
            value.to_decimal_string(),
            "170141183460469231731687303715884105728"
        );
    }

    #[test]
    fn signed_d192_boundary_is_exact_and_positive_overflow_fails_named() {
        let minimum = "-3138550867693340381917894711603833208051177722232017256448";
        let source = format!("(додати {minimum} 1)");
        let parsed = crate::parse(&source).expect("reader preserves the signed decimal boundary");
        let projected = project_ukr_decimal_integer_literals(&parsed, &source)
            .expect("-2^191 is representable by signed D192");
        let ExprKind::List(items) = &projected[0].kind else {
            panic!("expected one arithmetic form")
        };
        let ExprKind::BinaryNumber(value) = &items[1].kind else {
            panic!("expected exact D192 operand")
        };
        assert_eq!(value.numeric_domain_width(), Some(192));
        assert_eq!(value.to_decimal_string(), minimum);

        let positive_overflow = format!("(додати {} 1)", minimum.trim_start_matches('-'));
        let parsed = crate::parse(&positive_overflow).expect("positive boundary reader");
        let error = project_ukr_decimal_integer_literals(&parsed, &positive_overflow)
            .expect_err("positive 2^191 exceeds signed D192");
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
            .expect("source decimal integers become exact D12+ words");
        let lowered = crate::lower_program(&projected);
        assert!(
            matches!(
                &lowered[0].kind,
                ExprKind::DomainCall(identity, _)
                    if identity.width() == 5 && identity.packed_bits() == 0b10111
            ),
            "D5:10111 must be the immutable call head, not a rebindable Lisp name"
        );

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
            denominator
                .expect("nonintegral quotient has denominator")
                .to_unsigned_decimal_string(),
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
            denominator
                .expect("nonintegral sum has denominator")
                .to_unsigned_decimal_string(),
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

    #[test]
    fn український_парсер_виконує_точний_дріб_та_відхиляє_ділення_на_нуль() {
        // Справжній SENS обчислює весь чинний benchmark-файл, включно з D5,
        // а не Python чи тестова підміна числової семантики.
        let source = include_str!("../../../benchmarks/parser.lisp");
        let parsed = crate::parse(source).expect("читач розуміє весь український Lisp");
        let projected = project_ukr_decimal_integer_literals(&parsed, source)
            .expect("кожне десяткове ціле отримує власну D12+ ідентичність");
        let mut session = crate::Session::default();
        crate::load_core_library(&mut session).expect("чинне ядро SENS");
        let result = crate::eval_parsed_expressions(&projected, &mut session)
            .expect("SENS реально виконує усі вирази benchmark/parser.lisp");
        let crate::Value::NumericComposition(composition) = &result.value else {
            panic!("очікується точна D5 дробова композиція SENS")
        };
        let (_, numerator, denominator) = composition.as_parts();
        assert_eq!(numerator.to_unsigned_decimal_string(), "5");
        assert_eq!(
            denominator
                .expect("дробовий знаменник")
                .to_unsigned_decimal_string(),
            "336"
        );

        // Негативний закон виконує той самий інтерпретатор SENS.
        let invalid = "(частка 5 0)";
        let parsed = crate::parse(invalid).expect("читач не підміняє семантику");
        let projected = project_ukr_decimal_integer_literals(&parsed, invalid)
            .expect("нуль також є допустимим цілим операндом D12+");
        let error = crate::eval_parsed_expressions(&projected, &mut session)
            .err()
            .expect("SENS сам забороняє ділення на нуль");
        assert_eq!(error.kind, ErrorKind::DivisionByZero);
    }
}
