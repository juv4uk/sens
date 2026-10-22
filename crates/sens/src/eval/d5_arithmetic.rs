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
        0b01001 | 0b01010 | 0b01011 | 0b10110 | 0b10111 | 0b11010 | 0b11011
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
        // Ратифікований D5 NUMBERP — властивість точного D24+ об'єкта,
        // а не розпізнавання хостового Number, тексту D7 чи JSON.
        0b01001 => {
            if args.len() != 1 {
                Err(LanguageError::new(
                    ErrorKind::Arity,
                    format!("{identity}: D5 NUMBERP expects 1 argument; received {}", args.len()),
                    span,
                ))
            } else {
                Ok(Value::predicate_bit(crate::domain_numeric::is_domain_value(&args[0])))
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

#[cfg(test)]
mod exact_d5_numberp {
    use super::*;
    use crate::{BinaryNumber, Bit5, CoreD5, Exactness};

    fn d24(n: i32) -> Value {
        let word = (n as u32) & 0x00ff_ffff;
        let bits = (0..24).rev().map(|offset| ((word >> offset) & 1) as u8).collect::<Vec<_>>();
        Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap())
    }

    #[test]
    fn numberp_is_exact_d24_predicate_and_rejects_host_lookalikes() {
        let identity = CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b01001).unwrap()));
        let environment = Environment::root();
        let fraction = crate::domain_numeric::compute("/", &d24(7), &d24(2)).unwrap();
        for (argument, expected) in [
            (d24(7), true),
            (d24(-7), true),
            (fraction, true),
            (Value::Nil, false),
            (Value::String("7".into()), false),
            (Value::Number(7.0, Exactness::Exact), false),
        ] {
            let result = invoke(identity, &[argument], &environment, Span::default())
                .expect("D5 NUMBERP resident")
                .expect("D5 NUMBERP executes");
            assert_eq!(result.as_predicate_bit(), Some(expected));
        }
        let error = invoke(identity, &[], &environment, Span::default())
            .expect("D5 NUMBERP resident")
            .unwrap_err();
        assert_eq!(error.kind, ErrorKind::Arity);
    }
}
