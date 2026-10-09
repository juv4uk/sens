//! Direct execution for the ratified Core.D5 arithmetic roles.
//!
//! Domain identity selects the mechanism. Historical Function8/Sens8 slots
//! do not participate in this path.

use super::arithmetic;
use crate::{CoreDomainIdentity, Environment, ErrorKind, LanguageError, Rational, Span, Value};

pub(super) fn has_mechanism(identity: CoreDomainIdentity) -> bool {
    let CoreDomainIdentity::D5(word) = identity else {
        return false;
    };
    matches!(
        word.word().packed_bits(),
        0b01000 | 0b01001 | 0b01010 | 0b01011 | 0b10110 | 0b10111 | 0b11010 | 0b11011
    )
}
pub(super) fn invoke(
    identity: CoreDomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D5(word) = identity else {
        return None;
    };

    Some(match word.word().packed_bits() {
        0b01000 => zerop(args, span), // ZEROP
        0b01001 => numberp(args, span), // NUMBERP
        0b01010 => arithmetic::arithmetic_on_values("+", args, environment, span), // PLUS
        0b01011 => arithmetic::arithmetic_on_values("-", args, environment, span), // DIFFERENCE
        0b10110 => arithmetic::arithmetic_on_values("*", args, environment, span), // TIMES
        0b10111 => arithmetic::division_on_values(args, args.len(), environment, span), // QUOTIENT
        0b11010 => arithmetic::comparison_on_values("<", args, span), // LESSP
        0b11011 => arithmetic::comparison_on_values(">", args, span), // GREATERP
        _ => return None,
    })
}

fn one_arg<'a>(args: &'a [Value], label: &str, span: Span) -> Result<&'a Value, LanguageError> {
    if args.len() != 1 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            format!("{label}: expected exactly 1 argument, received {}", args.len()),
            span,
        ));
    }
    Ok(&args[0])
}

fn numberp(args: &[Value], span: Span) -> Result<Value, LanguageError> {
    let value = one_arg(args, "D5:01001", span)?;
    Ok(Value::predicate_bit(matches!(
        value,
        Value::Number(_, _) | Value::Rational(_) | Value::BinaryNumber(_)
    )))
}

fn zerop(args: &[Value], span: Span) -> Result<Value, LanguageError> {
    let value = one_arg(args, "D5:01000", span)?;
    let yes = match value {
        Value::Number(number, _) => number.is_finite() && number.abs() <= 3_f64 / 1_000_000_f64,
        Value::Rational(number) => {
            let tolerance = Rational::new(3, 1_000_000).expect("valid tolerance");
            let negative = -tolerance.clone();
            number >= &negative && number <= &tolerance
        }
        Value::BinaryNumber(number) => number.is_zero(),
        other => {
            return Err(LanguageError::new(
                ErrorKind::Type,
                format!("D5:01000 expects an admitted numeric value, received {other}"),
                span,
            ))
        }
    };
    Ok(Value::predicate_bit(yes))
}
