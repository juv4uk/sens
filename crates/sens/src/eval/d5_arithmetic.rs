//! Direct execution for the ratified Core.D5 arithmetic roles.
//!
//! Domain identity selects the mechanism. Historical flat eight-bit slots
//! do not participate in this path.

use super::arithmetic;
use crate::{CoreDomainIdentity, Environment, ErrorKind, LanguageError, Span, Value};

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
        // D5:01000 ZEROP: нуль лише в точному D24+ числовому домені.
        // D7-цифри, голі host-числа і D1/D3 ніколи не стають нулем.
        // Канонічна дробова композиція з ненульовим знаменником
        // зберігає ненульовий чисельник; нуль є BinaryNumber.
        0b01000 => {
            if args.len() != 1 {
                Err(LanguageError::new(
                    ErrorKind::Arity,
                    format!(
                        "{identity}: D5 ZEROP expects 1 argument; received {}",
                        args.len()
                    ),
                    span,
                ))
            } else if !crate::domain_numeric::is_domain_value(&args[0]) {
                Err(LanguageError::new(
                    ErrorKind::Type,
                    "D5 ZEROP requires one exact D12+ numeric argument",
                    span,
                ))
            } else {
                Ok(Value::predicate_bit(matches!(
                    &args[0],
                    Value::BinaryNumber(number) if number.is_zero()
                )))
            }
        }
        // Ратифікований D5 NUMBERP — властивість точного D12+ об'єкта,
        // а не розпізнавання хостового Number, тексту D7 чи JSON.
        0b01001 => {
            if args.len() != 1 {
                Err(LanguageError::new(
                    ErrorKind::Arity,
                    format!(
                        "{identity}: D5 NUMBERP expects 1 argument; received {}",
                        args.len()
                    ),
                    span,
                ))
            } else {
                Ok(Value::predicate_bit(
                    crate::domain_numeric::is_domain_value(&args[0]),
                ))
            }
        }
        0b01010 => arithmetic::arithmetic_on_values("+", args, environment, span), // PLUS
        0b01011 => arithmetic::arithmetic_on_values("-", args, environment, span), // DIFFERENCE
        0b10110 => arithmetic::arithmetic_on_values("*", args, environment, span), // TIMES
        0b10111 => arithmetic::division_on_values(args, args.len(), environment, span), // QUOTIENT
        0b11010 => arithmetic::comparison_on_values("<", args, span),              // LESSP
        0b11011 => arithmetic::comparison_on_values(">", args, span),              // GREATERP
        _ => return None,
    })
}
