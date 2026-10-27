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
