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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{BinaryNumber, Bit4, Bit5, CoreD4, CoreD5, Exactness};

    fn d5(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(bits).unwrap()))
    }

    fn n(value: f64) -> Value {
        Value::Number(value, Exactness::Exact)
    }

    #[test]
    fn six_ratified_d5_numeric_roles_execute_directly() {
        let env = Environment::root();
        let span = Span::default();

        assert_eq!(
            invoke(d5(0b01010), &[n(1.0), n(2.0), n(3.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "6"
        );
        assert_eq!(
            invoke(d5(0b01011), &[n(7.0), n(2.0), n(1.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "4"
        );
        let less_yes = invoke(d5(0b11010), &[n(2.0), n(3.0)], &env, span)
            .unwrap()
            .unwrap();
        let less_no = invoke(d5(0b11010), &[n(3.0), n(2.0)], &env, span)
            .unwrap()
            .unwrap();
        let greater_yes = invoke(d5(0b11011), &[n(3.0), n(2.0)], &env, span)
            .unwrap()
            .unwrap();
        assert_eq!(less_yes.as_predicate_bit(), Some(true));
        assert_eq!(less_no.as_predicate_bit(), Some(false));
        assert_eq!(greater_yes.as_predicate_bit(), Some(true));
        assert_eq!(
            invoke(d5(0b10110), &[n(2.0), n(3.0), n(4.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "24"
        );
        assert_eq!(
            invoke(d5(0b10111), &[n(6.0), n(3.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "2"
        );
    }

    fn q(numerator: i64, denominator: i64) -> Value {
        Value::Rational(crate::Rational::new(numerator, denominator).unwrap())
    }

    fn call_d5(bits: u8, args: &[Value]) -> Result<Value, LanguageError> {
        invoke(
            d5(bits),
            args,
            &Environment::root(),
            Span::default(),
        )
        .expect("ratified D5 arithmetic resident must dispatch")
    }

    #[test]
    fn zerop_numberp_preserve_tolerance_entailment_and_carriers() {
        let boundary = 3_f64 / 1_000_000_f64;
        let outside = 31_f64 / 10_000_000_f64;

        for value in [
            Value::Number(0_f64, Exactness::Exact),
            Value::Number(boundary, Exactness::Inexact),
            Value::Number(-boundary, Exactness::Inexact),
            q(3, 1_000_000),
            q(-3, 1_000_000),
            Value::BinaryNumber(BinaryNumber::zero()),
        ] {
            assert_eq!(
                call_d5(0b01000, std::slice::from_ref(&value))
                    .unwrap()
                    .as_predicate_bit(),
                Some(true),
                "ZEROP boundary: {value}"
            );
            assert_eq!(
                call_d5(0b01001, std::slice::from_ref(&value))
                    .unwrap()
                    .as_predicate_bit(),
                Some(true),
                "ZEROP(x)=1 must entail NUMBERP(x)=1 for {value}"
            );
        }

        for value in [
            Value::Number(outside, Exactness::Inexact),
            Value::Number(-outside, Exactness::Inexact),
            q(31, 10_000_000),
            q(-31, 10_000_000),
            Value::BinaryNumber(BinaryNumber::one()),
        ] {
            assert_eq!(
                call_d5(0b01000, std::slice::from_ref(&value))
                    .unwrap()
                    .as_predicate_bit(),
                Some(false)
            );
            assert_eq!(
                call_d5(0b01001, std::slice::from_ref(&value))
                    .unwrap()
                    .as_predicate_bit(),
                Some(true)
            );
        }

        let symbol = Value::Symbol(std::rc::Rc::from("x"));
        assert_eq!(
            call_d5(0b01001, std::slice::from_ref(&symbol))
                .unwrap()
                .as_predicate_bit(),
            Some(false)
        );
        let error = call_d5(0b01000, &[symbol]).expect_err("ZEROP must reject nonnumeric");
        assert_eq!(error.kind, ErrorKind::Type);
    }

    #[test]
    fn d5_numeric_predicates_require_one_argument() {
        for bits in [0b01000, 0b01001] {
            assert_eq!(call_d5(bits, &[]).unwrap_err().kind, ErrorKind::Arity);
            assert_eq!(
                call_d5(bits, &[n(0_f64), n(0_f64)]).unwrap_err().kind,
                ErrorKind::Arity
            );
        }
    }

    #[test]
    fn d5_order_rejects_inexact_operands_instead_of_manufacturing_truth() {
        let error = call_d5(
            0b11010,
            &[
                Value::Number(2.0, Exactness::Inexact),
                Value::Number(3.0, Exactness::Inexact),
            ],
        )
        .expect_err("inexact order has no exact PredicateBit answer");
        assert_eq!(error.kind, crate::ErrorKind::Type);
    }

#[test]
    fn additive_and_multiplicative_siblings_follow_local_inverse_orientation_laws() {
        // #3003: this is Core.D5-local evidence.  The exact-Q Core-Math
        // factorization is only a counter-domain comparison and is not used
        // to select these identities or define their meaning.
        let corpus = [
            (-3, 1),
            (-1, 2),
            (0, 1),
            (1, 3),
            (2, 1),
            (5, 2),
        ];

        for &(a_num, a_den) in &corpus {
            for &(b_num, b_den) in &corpus {
                let a = q(a_num, a_den);
                let b = q(b_num, b_den);

                let difference = call_d5(0b01011, &[a.clone(), b.clone()]).unwrap();
                let additive_inverse = q(-b_num, b_den);
                let plus_inverse =
                    call_d5(0b01010, &[a.clone(), additive_inverse]).unwrap();
                assert_eq!(
                    difference.to_string(),
                    plus_inverse.to_string(),
                    "Core.D5 DIFFERENCE must equal PLUS with independently constructed additive inverse for {a_num}/{a_den}, {b_num}/{b_den}"
                );

                let quotient = call_d5(0b10111, &[a.clone(), b.clone()]);
                if b_num == 0 {
                    let error = quotient.expect_err(
                        "Core.D5 QUOTIENT must preserve division-by-zero partiality",
                    );
                    assert_eq!(error.kind, crate::ErrorKind::DivisionByZero);
                } else {
                    let quotient = quotient.unwrap();
                    let multiplicative_inverse = q(b_den, b_num);
                    let times_inverse =
                        call_d5(0b10110, &[a.clone(), multiplicative_inverse]).unwrap();
                    assert_eq!(
                        quotient.to_string(),
                        times_inverse.to_string(),
                        "Core.D5 QUOTIENT must equal TIMES with independently constructed multiplicative inverse for {a_num}/{a_den}, {b_num}/{b_den}"
                    );
                }
            }
        }
    }

    #[test]
    fn arithmetic_sibling_law_does_not_mint_a_d4_parent() {
        let d4 = CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0101).unwrap()));
        assert!(
            invoke(
                d4,
                &[q(1, 2), q(1, 3)],
                &Environment::root(),
                Span::default(),
            )
            .is_none(),
            "local D5 sibling law must not create a D4 arithmetic parent"
        );
    }

    #[test]
    fn superseded_arithmetic_coordinates_do_not_dispatch_as_arithmetic() {
        for bits in [0b01110, 0b01111, 0b10010, 0b10011] {
            assert!(
                invoke(d5(bits), &[n(2.0), n(1.0)], &Environment::root(), Span::default()).is_none(),
                "superseded D5 arithmetic coordinate {bits:05b} must not dispatch through d5_arithmetic"
            );
        }
    }

    #[test]
    fn same_payload_in_d4_does_not_acquire_d5_arithmetic_meaning() {
        let d4 = CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1010).unwrap()));
        assert!(invoke(d4, &[n(1.0), n(2.0)], &Environment::root(), Span::default()).is_none());
    }

    #[test]
    fn non_arithmetic_d5_coordinate_is_not_minted_by_width() {
        assert!(invoke(
            d5(0b00000),
            &[n(1.0)],
            &Environment::root(),
            Span::default()
        )
        .is_none());
    }
}
