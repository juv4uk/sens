//! Direct execution for the ratified Core.D5 numeric predicates.
//!
//! 01000 ZEROP and 01001 NUMBERP are a typed entailment family.
//! The suffix bit has no universal meaning.

use crate::{
    CoreDomainIdentity, ErrorKind, Exactness, LanguageError, Rational, Span, Value,
};

const HISTORICAL_ZERO_EPSILON: f64 = 3.0e-6;

fn rational_within_historical_zero_tolerance(number: &Rational) -> bool {
    let epsilon = Rational::new(3, 1_000_000).expect("3/1_000_000 is a valid rational");
    let magnitude = if number.is_negative() {
        -number.clone()
    } else {
        number.clone()
    };
    magnitude <= epsilon
}

pub(super) fn invoke(
    identity: CoreDomainIdentity,
    args: &[Value],
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D5(word) = identity else {
        return None;
    };

    let bits = word.word().packed_bits();
    if !matches!(bits, 0b01000 | 0b01001) {
        return None;
    }

    if args.len() != 1 {
        return Some(Err(LanguageError::new(
            ErrorKind::Arity,
            format!(
                "{identity}: exact D5 numeric predicate expects 1 argument; received {}",
                args.len()
            ),
            span,
        )));
    }

    let value = &args[0];
    Some(match bits {
        0b01001 => Ok(Value::predicate_bit(matches!(
            value,
            Value::Number(_, _) | Value::Rational(_) | Value::BinaryNumber(_)
        ))), // NUMBERP

        0b01000 => {
            let holds = match value {
                Value::BinaryNumber(number) => number.is_zero(),
                Value::Rational(number) => rational_within_historical_zero_tolerance(number),
                Value::Number(number, Exactness::Exact | Exactness::Inexact) => {
                    number.abs() <= HISTORICAL_ZERO_EPSILON
                }
                _ => {
                    return Some(Err(LanguageError::new(
                        ErrorKind::Type,
                        format!("{identity}: ZEROP expects a numeric carrier"),
                        span,
                    )));
                }
            };
            Ok(Value::predicate_bit(holds))
        }
        _ => unreachable!(),
    })
}
