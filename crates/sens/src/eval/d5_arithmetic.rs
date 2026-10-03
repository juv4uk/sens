//! Direct execution for the ratified Core.D5 arithmetic roles.
//!
//! Domain identity selects the mechanism. Historical Function8/Sens8 slots
//! do not participate in this path.

use super::arithmetic;
use crate::{CoreDomainIdentity, Environment, LanguageError, Span, Value};

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
        0b01110 => arithmetic::comparison_on_values("<", args, span), // LESSP
        0b01111 => arithmetic::comparison_on_values(">", args, span), // GREATERP
        0b10010 => arithmetic::arithmetic_on_values("*", args, environment, span), // TIMES
        0b10011 => arithmetic::division_on_values(args, args.len(), environment, span), // QUOTIENT
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
            invoke(d5(0b01110), &[n(2.0), n(3.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "1"
        );
        assert_eq!(
            invoke(d5(0b01111), &[n(3.0), n(2.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "1"
        );
        assert_eq!(
            invoke(d5(0b10010), &[n(2.0), n(3.0), n(4.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "24"
        );
        assert_eq!(
            invoke(d5(0b10011), &[n(6.0), n(3.0)], &env, span)
                .unwrap().unwrap().to_string(),
            "2"
        );
    }

    #[test]
    fn same_payload_in_d4_does_not_acquire_d5_arithmetic_meaning() {
        let d4 = CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1010).unwrap()));
        assert!(invoke(d4, &[n(1.0), n(2.0)], &Environment::root(), Span::default()).is_none());
    }

    #[test]
    fn unassigned_d5_coordinate_is_not_minted_by_width() {
        assert!(invoke(
            d5(0b00000),
            &[n(1.0)],
            &Environment::root(),
            Span::default()
        )
        .is_none());
    }
}
