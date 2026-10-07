//! Exact mechanisms for the first admitted D6 arithmetic residents.
//!
//! Semantic authority: #3393 / Contract 11.8.
//! Mechanism authority: #3394.
//!
//! ADD1/SUB1 do not mint a new arithmetic backend. They are admitted as
//! LOWER_DOMAIN_COMPOSITION over the already-admitted D5 PLUS/DIFFERENCE laws
//! with exact integer 1.

use crate::{
    Bit5, CoreD5, CoreDomainIdentity, Environment, ErrorKind, LanguageError, Rational, Span, Value,
};

fn d5(bits: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D5(CoreD5::from_word(
        Bit5::new(bits).expect("D5 arithmetic coordinate"),
    ))
}

pub(super) fn invoke(
    identity: CoreDomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D6(word) = identity else {
        return None;
    };

    let bits = word.word().packed_bits();
    if !matches!(bits, 0b001110 | 0b001111) {
        return None;
    }

    if args.len() != 1 {
        return Some(Err(LanguageError::new(
            ErrorKind::Arity,
            format!(
                "{identity}: exact D6 ADD1/SUB1 mechanism expects 1 argument; received {}",
                args.len()
            ),
            span,
        )));
    }

    let composed_args = [
        args[0].clone(),
        Value::Rational(Rational::integer(1)),
    ];
    let d5_identity = match bits {
        0b001110 => d5(0b01010), // ADD1 = D5 PLUS(x, 1)
        0b001111 => d5(0b01011), // SUB1 = D5 DIFFERENCE(x, 1)
        _ => unreachable!(),
    };

    Some(
        super::d5_arithmetic::invoke(d5_identity, &composed_args, environment, span)
            .expect("selected D5 arithmetic resident has an admitted mechanism"),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit6, CoreD6};

    fn d6(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(bits).unwrap()))
    }

    fn q(numerator: i64, denominator: i64) -> Value {
        Value::Rational(Rational::new(numerator, denominator).unwrap())
    }

    #[test]
    fn add1_and_sub1_are_exact_d5_compositions() {
        let env = Environment::root();
        let span = Span::default();

        for (bits, input, expected) in [
            (0b001110, q(1, 2), "3/2"),
            (0b001110, q(-2, 1), "-1"),
            (0b001111, q(1, 2), "-1/2"),
            (0b001111, q(-2, 1), "-3"),
        ] {
            let value = invoke(d6(bits), &[input], &env, span)
                .expect("admitted D6 mechanism")
                .expect("exact D6 arithmetic");
            assert_eq!(value.to_string(), expected, "D6:{bits:06b}");
        }
    }
}
