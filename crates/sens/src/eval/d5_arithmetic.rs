//! Direct execution for the ratified Core.D5 arithmetic roles.
//!
//! Domain identity selects the mechanism. Historical Function8/Sens8 slots
//! do not participate in this path.

use super::arithmetic;
use crate::{CoreDomainIdentity, Environment, LanguageError, Span, Value};

pub(super) fn has_mechanism(identity: CoreDomainIdentity) -> bool {
    let CoreDomainIdentity::D5(word) = identity else {
        return false;
    };
    matches!(
        word.word().packed_bits(),
        0b01010 | 0b01011 | 0b10110 | 0b10111 | 0b11010 | 0b11011
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
        0b01010 => arithmetic::arithmetic_on_values("+", args, environment, span), // PLUS
        0b01011 => arithmetic::arithmetic_on_values("-", args, environment, span), // DIFFERENCE
        0b10110 => arithmetic::arithmetic_on_values("*", args, environment, span), // TIMES
        0b10111 => arithmetic::division_on_values(args, args.len(), environment, span), // QUOTIENT
        0b11010 => arithmetic::comparison_on_values("<", args, span), // LESSP
        0b11011 => arithmetic::comparison_on_values(">", args, span), // GREATERP
        _ => return None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bit4, Bit5, CoreD4, CoreD5, Exactness};

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
        assert_eq!(
            invoke(d5(0b11010), &[n(2.0), n(3.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "1"
        );
        assert_eq!(
            invoke(d5(0b11011), &[n(3.0), n(2.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "1"
        );
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
