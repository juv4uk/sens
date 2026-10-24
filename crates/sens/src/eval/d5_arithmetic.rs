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

#[cfg(test)]
mod exact_d5_numberp {
    use super::*;
    use crate::{BinaryNumber, Bit5, CoreD5, Exactness};

    fn d24(n: i32) -> Value {
        let word = (n as u32) & 0x00ff_ffff;
        let bits = (0..24)
            .rev()
            .map(|offset| ((word >> offset) & 1) as u8)
            .collect::<Vec<_>>();
        Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap())
    }

    fn d12(n: i16) -> Value {
        let word = (n as u16) & 0x0fff;
        let bits = (0..12)
            .rev()
            .map(|offset| ((word >> offset) & 1) as u8)
            .collect::<Vec<_>>();
        Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(12, &bits).unwrap())
    }

    #[test]
    fn zerop_is_exact_d12_plus_law_and_never_coerces_text_or_host_number() {
        let identity = CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b01000).unwrap()));
        let environment = Environment::root();
        let fraction = crate::domain_numeric::compute("/", &d24(7), &d24(2)).unwrap();
        let fraction_d12 = crate::domain_numeric::compute("/", &d12(7), &d12(2)).unwrap();
        for (argument, expected) in [
            (d24(0), true),
            (d24(7), false),
            (d24(-7), false),
            (fraction, false),
            (d12(0), true),
            (d12(7), false),
            (d12(-7), false),
            (fraction_d12, false),
        ] {
            let actual = invoke(identity, &[argument], &environment, Span::default())
                .expect("D5 ZEROP resident")
                .expect("D5 ZEROP executes");
            assert_eq!(actual.as_predicate_bit(), Some(expected));
        }
        for input in [
            Value::Nil,
            Value::predicate_bit(false),
            Value::String("0".into()),
            Value::Number(0.0, Exactness::Exact),
        ] {
            let error = invoke(identity, &[input], &environment, Span::default())
                .expect("D5 ZEROP resident")
                .expect_err("non-domain value must not be coerced into numeric zero");
            assert_eq!(error.kind, ErrorKind::Type);
        }
        for args in [Vec::<Value>::new(), vec![d24(0), d24(0)]] {
            assert_eq!(
                invoke(identity, &args, &environment, Span::default())
                    .expect("D5 ZEROP resident")
                    .unwrap_err()
                    .kind,
                ErrorKind::Arity
            );
        }

        // Справжній SENS eval, не хост-оракул і не Python/JSON.
        let mut session = crate::Session::default();
        crate::load_core_library(&mut session).expect("чинний SENS core");
        for (source, expected) in [
            ("(нуль? 0)", true),
            ("(нуль? 7)", false),
            ("(нуль? -7)", false),
        ] {
            let result = crate::eval_program(source, &mut session)
                .unwrap_or_else(|e| panic!("{source}: {e}"));
            assert_eq!(result.value.as_predicate_bit(), Some(expected), "{source}");
        }
    }

    #[test]
    fn numberp_is_exact_d12_plus_predicate_and_rejects_host_lookalikes() {
        let identity = CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b01001).unwrap()));
        let environment = Environment::root();
        let fraction = crate::domain_numeric::compute("/", &d24(7), &d24(2)).unwrap();
        let fraction_d12 = crate::domain_numeric::compute("/", &d12(7), &d12(2)).unwrap();
        for (argument, expected) in [
            (d24(7), true),
            (d24(-7), true),
            (fraction, true),
            (d12(7), true),
            (d12(-7), true),
            (fraction_d12, true),
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
