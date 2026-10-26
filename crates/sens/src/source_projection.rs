//! Projection of human-facing decimal numbers into exact SENS D12+ values.
//!
//! The source spelling supplies the digits; it is not itself a domain identity.
//! This boundary is shared by embedders. It never promotes D1-D10 words or
//! host numbers into arithmetic. Rational literals lower to the admitted D5
//! Ukrainian `частка` operation; their integer components are exact D12+ words.
//!
//! Integer and rational components are source-qualified to the smallest signed
//! D12/D24/D48/D96/D192 word that contains them. Within one connected D5 numeric
//! expression tree, all numeric components receive the same widest required
//! domain. This avoids mixed-Dn operands and never routes exact input through a
//! host integer or float.

use crate::syntax::{Expr, ExprKind, Span};
use crate::{BinaryNumber, ErrorKind, LanguageError};
use std::rc::Rc;

/// Project exact decimal integer and rational literals before evaluation.
///
/// Numeric literals in one connected D5 call tree share the widest required
/// numeric domain; independent values retain the smallest exact domain no
/// narrower than the caller's explicit projection floor.
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
                Span {
                    start: 0,
                    end: source.len(),
                },
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

fn integer_width(token: &str, span: Span, minimum_width: usize) -> Result<usize, LanguageError> {
    let (negative, magnitude) = decimal_magnitude_bits(token, span)?;
    [12usize, 24, 48, 96, 192]
        .into_iter()
        .filter(|width| *width >= minimum_width)
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

fn rational_component_spelling(value: &crate::Rational) -> (String, String) {
    let spelling = value.to_string();
    spelling
        .split_once('/')
        .map_or((spelling.clone(), "1".to_string()), |(n, d)| {
            (n.to_string(), d.to_string())
        })
}

fn exact_source_rational(expr: &Expr, source: &str) -> Option<crate::Rational> {
    if !matches!(&expr.kind, ExprKind::Number(_, crate::Exactness::Exact)) {
        return None;
    }
    let token = source.get(expr.span.start..expr.span.end)?;
    let normalized = token.replace(',', ".").replace(['е', 'Е'], "e");
    crate::Rational::from_decimal_literal(&normalized).ok()
}

fn rational_required_width(
    value: &crate::Rational,
    span: Span,
    minimum_width: usize,
) -> Result<usize, LanguageError> {
    let (numerator, denominator) = rational_component_spelling(value);
    Ok(
        integer_width(&numerator, span, minimum_width)?.max(integer_width(
            &denominator,
            span,
            minimum_width,
        )?),
    )
}

fn project_rational(
    value: &crate::Rational,
    span: Span,
    inherited_width: Option<usize>,
    minimum_width: usize,
) -> Result<ExprKind, LanguageError> {
    let required = rational_required_width(value, span, minimum_width)?;
    let width = inherited_width.unwrap_or(required).max(required);
    let (numerator, denominator) = rational_component_spelling(value);
    let numerator = project_integer(&numerator, span, width, minimum_width)?;
    let denominator = project_integer(&denominator, span, width, minimum_width)?;
    let quotient = crate::semantic_registry_export::admitted_core_domain_for_surface("частка")
        .filter(|identity| identity.width() == 5)
        .ok_or_else(|| {
            LanguageError::new(
                ErrorKind::MechanismUnavailable,
                "exact source ratio has no admitted D5 quotient identity",
                span,
            )
        })?;
    Ok(ExprKind::DomainCall(
        quotient,
        vec![numerator, denominator].into(),
    ))
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
    if let ExprKind::Rational(value) = &expr.kind {
        return rational_required_width(value, expr.span, minimum_width).map(Some);
    }
    if let Some(value) = exact_source_rational(expr, source) {
        let (numerator, denominator) = rational_component_spelling(&value);
        return Ok(Some(
            integer_width(&numerator, expr.span, minimum_width)?.max(integer_width(
                &denominator,
                expr.span,
                minimum_width,
            )?),
        ));
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
    if let ExprKind::Rational(value) = &expr.kind {
        return Ok(Expr {
            kind: project_rational(value, expr.span, inherited_math_width, minimum_width)?,
            span: expr.span,
        });
    }
    if let Some(value) = exact_source_rational(expr, source) {
        let spelling = value.to_string();
        let kind = if spelling.contains('/') {
            project_rational(&value, expr.span, inherited_math_width, minimum_width)?
        } else {
            let required = integer_width(&spelling, expr.span, minimum_width)?;
            project_integer(
                &spelling,
                expr.span,
                inherited_math_width.unwrap_or(required),
                minimum_width,
            )?
            .kind
        };
        return Ok(Expr {
            kind,
            span: expr.span,
        });
    }

    let kind = match &expr.kind {
        ExprKind::List(items) if is_d5_call(expr) => {
            let required = required_width_in_math_tree(expr, source, 0, minimum_width)?
                .unwrap_or(minimum_width);
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
    fn explicit_d12_projection_keeps_signed_boundaries_and_widens_exactly() {
        let source = "(приклад 0 1 -1 2047 -2048 2048 -2049)";
        let parsed = crate::parse(source).expect("source parses");
        let projected =
            project_ukr_decimal_integer_literals_with_minimum_width(&parsed, source, 12)
                .expect("D12 source integers project to exact admitted numeric widths");
        let ExprKind::List(items) = &projected[0].kind else {
            panic!("expected one list")
        };
        let values: Vec<_> = items
            .iter()
            .skip(1)
            .map(|expr| match &expr.kind {
                ExprKind::BinaryNumber(number) => number.clone(),
                other => panic!("expected a domain-qualified number, got {other:?}"),
            })
            .collect();
        assert_eq!(
            values
                .iter()
                .map(BinaryNumber::numeric_domain_width)
                .collect::<Vec<_>>(),
            vec![
                Some(12),
                Some(12),
                Some(12),
                Some(12),
                Some(12),
                Some(24),
                Some(24)
            ]
        );
        assert_eq!(
            values
                .iter()
                .map(BinaryNumber::to_decimal_string)
                .collect::<Vec<_>>(),
            vec!["0", "1", "-1", "2047", "-2048", "2048", "-2049"]
        );

        let positive_max = values[3].exact_numeric_domain_bits().unwrap();
        let negative_min = values[4].exact_numeric_domain_bits().unwrap();
        assert_eq!(positive_max, vec![0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]);
        assert_eq!(negative_min, vec![1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
    }

    #[test]
    fn explicit_d12_projection_runs_same_domain_arithmetic_and_carries_without_wrap() {
        let source = "(додати 2047 1)";
        let parsed = crate::parse(source).expect("source parses");
        let projected =
            project_ukr_decimal_integer_literals_with_minimum_width(&parsed, source, 12)
                .expect("each literal starts in exact D12");
        let ExprKind::List(items) = &projected[0].kind else {
            panic!("expected one addition form")
        };
        assert!(
            items.iter().skip(1).all(|expr| matches!(
                &expr.kind,
                ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(12)
            )),
            "both source operands must retain exact D12 identity"
        );

        let mut session = crate::Session::default();
        crate::load_core_library(&mut session).expect("SENS Core loads");
        let result = crate::eval_parsed_expressions(&projected, &mut session)
            .expect("SENS computes the exact result without modulo-4096 wrapping");
        let crate::Value::BinaryNumber(ref sum) = result.value else {
            panic!("D12 addition must return an exact numeric word")
        };
        assert_eq!(sum.numeric_domain_width(), Some(24));
        assert_eq!(sum.to_decimal_string(), "2048");

        let same_magnitude_d24 = BinaryNumber::from_numeric_domain_bits(24, &{
            let mut bits = vec![0; 24];
            bits[22] = 1;
            bits
        })
        .expect("explicit D24 2");
        let d12_two = values_as_d12_two();
        assert_ne!(d12_two, same_magnitude_d24);
        assert_eq!(d12_two.add_admitted_numeric(&same_magnitude_d24), None);
    }

    fn values_as_d12_two() -> BinaryNumber {
        let parsed = crate::parse("2").expect("simple integer source parses");
        let projected = project_ukr_decimal_integer_literals_with_minimum_width(&parsed, "2", 12)
            .expect("explicit D12 projection");
        match &projected[0].kind {
            ExprKind::BinaryNumber(number) => number.clone(),
            other => panic!("expected D12 number, got {other:?}"),
        }
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
    fn rational_and_integer_literals_share_the_widest_domain_in_one_math_tree() {
        let source = "(додати 1е-7 1е-20)";
        let parsed = crate::parse(source).expect("decimal and Ukrainian exponent parse exactly");
        let projected =
            project_ukr_decimal_integer_literals_with_minimum_width(&parsed, source, 12)
                .expect("all ratio components fit D12+");

        fn widths(expression: &Expr, found: &mut Vec<usize>) {
            match &expression.kind {
                ExprKind::BinaryNumber(number) => {
                    found.push(number.numeric_domain_width().expect("numeric domain"));
                }
                ExprKind::DomainCall(_, arguments) => {
                    for argument in arguments.iter() {
                        widths(argument, found);
                    }
                }
                ExprKind::List(items) => {
                    for item in items.iter() {
                        widths(item, found);
                    }
                }
                _ => {}
            }
        }

        let mut found = Vec::new();
        widths(&projected[0], &mut found);
        assert!(!found.is_empty());
        assert!(found.iter().all(|width| *width == 96), "{found:?}");

        let source = "(додати 2.0 1е-20)";
        let parsed = crate::parse(source).expect("exact decimal integer and exponent parse");
        let projected =
            project_ukr_decimal_integer_literals_with_minimum_width(&parsed, source, 12)
                .expect("exact decimal values must share the required width");
        let mut found = Vec::new();
        widths(&projected[0], &mut found);
        assert!(!found.is_empty());
        assert!(found.iter().all(|width| *width == 96), "{found:?}");
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
