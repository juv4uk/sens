//! Exact mechanisms for the first admitted D6 arithmetic residents.
//!
//! Semantic authority: #3393 / Contract 11.8.
//! Mechanism authority: #3394.
//!
//! ADD1/SUB1/NEG do not mint another numeric authority. They compose the
//! admitted D5 PLUS/DIFFERENCE laws with exact 0 or 1 in the operand's
//! already admitted D12+ domain. D6 identity and its law remain SENS-owned.

use crate::{
    BinaryNumber, Bit5, CoreD5, CoreDomainIdentity, Environment, ErrorKind, LanguageError, Span,
    Value,
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
    if !matches!(bits, 0b001110 | 0b001111 | 0b010010 | 0b111110) {
        return None;
    }

    // D6:111110 INTEGERP читає тільки явний D12+ числовий тип.
    // RATIO(p,1) канонічно стає BinaryNumber, а дріб — NumericComposition.
    // Ні #q2, ні D8 wire, ні Unicode не визначають математичну істину.
    if bits == 0b111110 {
        if args.len() != 1 {
            return Some(Err(LanguageError::new(
                ErrorKind::Arity,
                format!(
                    "{identity}: D6 INTEGERP expects 1 argument; received {}",
                    args.len()
                ),
                span,
            )));
        }
        return Some(Ok(Value::predicate_bit(matches!(
            &args[0],
            Value::BinaryNumber(number) if number.numeric_domain_width().is_some()
        ))));
    }

    if args.len() != 1 {
        return Some(Err(LanguageError::new(
            ErrorKind::Arity,
            format!(
                "{identity}: exact D6 ADD1/SUB1/NEG mechanism expects 1 argument; received {}",
                args.len()
            ),
            span,
        )));
    }

    // The old implementation inserted an unqualified Rational(1), silently
    // crossing the D24+ admission boundary. ADD1/SUB1 are operators in D6,
    // but their numeric *operands* must be explicitly qualified D12+ values.
    let width = match &args[0] {
        Value::BinaryNumber(number) => number.numeric_domain_width(),
        Value::NumericComposition(composition) => Some(composition.domain_width()),
        _ => None,
    };
    let Some(width) = width else {
        return Some(Err(LanguageError::new(
            ErrorKind::Type,
            "D6 ADD1/SUB1/NEG requires a D12+ numeric operand",
            span,
        )));
    };
    // D6 NEG uses the exact D5 DIFFERENCE(0,x) law, not a host sign bit,
    // a D7 glyph, or an unqualified numeric literal. Domain/width survives
    // the boundary; the D5 arithmetic law handles overflow and fractions.
    let mut constant_bits = vec![0; width];
    if bits != 0b010010 {
        constant_bits[width - 1] = 1;
    }
    let constant = BinaryNumber::from_numeric_domain_bits(width, &constant_bits)
        .expect("D12+ domain width from qualified operand");
    let composed_args = if bits == 0b010010 {
        [Value::BinaryNumber(constant), args[0].clone()]
    } else {
        [args[0].clone(), Value::BinaryNumber(constant)]
    };
    let d5_identity = match bits {
        0b001110 => d5(0b01010), // ADD1 = D5 PLUS(x, 1)
        0b001111 => d5(0b01011), // SUB1 = D5 DIFFERENCE(x, 1)
        0b010010 => d5(0b01011), // NEG = D5 DIFFERENCE(0, x)
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

    fn d24(n: i32) -> Value {
        let mut bits = vec![0; 24];
        let encoded = (i64::from(n) & 0x00ff_ffff) as u32;
        for i in 0..24 {
            bits[23 - i] = ((encoded >> i) & 1) as u8;
        }
        Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap())
    }

    fn d12(n: i32) -> Value {
        assert!((-2048..=2047).contains(&n));
        let encoded = if n < 0 { (1_i32 << 12) + n } else { n };
        let bits = (0..12)
            .rev()
            .map(|shift| ((encoded >> shift) & 1) as u8)
            .collect::<Vec<_>>();
        Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(12, &bits).unwrap())
    }

    #[test]
    fn d6_unit_arithmetic_admits_d12_and_promotes_signed_boundaries() {
        let env = Environment::root();
        let add1 = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b001110).unwrap(),
        ));
        let sub1 = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b001111).unwrap(),
        ));
        let neg = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b010010).unwrap(),
        ));
        let integerp = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b111110).unwrap(),
        ));

        let assert_integer = |value: Value, width: usize, expected: &str| {
            let Value::BinaryNumber(ref number) = value else {
                panic!("D6 arithmetic must return an exact numeric-domain value");
            };
            assert_eq!(number.numeric_domain_width(), Some(width));
            assert_eq!(number.to_decimal_string(), expected);
            assert_eq!(number.exact_numeric_domain_bits().unwrap().len(), width);
        };

        assert_integer(
            invoke(add1, &[d12(7)], &env, Span::default())
                .unwrap()
                .unwrap(),
            12,
            "8",
        );
        assert_integer(
            invoke(sub1, &[d12(7)], &env, Span::default())
                .unwrap()
                .unwrap(),
            12,
            "6",
        );
        assert_integer(
            invoke(add1, &[d12(2047)], &env, Span::default())
                .unwrap()
                .unwrap(),
            24,
            "2048",
        );
        assert_integer(
            invoke(sub1, &[d12(-2048)], &env, Span::default())
                .unwrap()
                .unwrap(),
            24,
            "-2049",
        );
        assert_integer(
            invoke(neg, &[d12(-2048)], &env, Span::default())
                .unwrap()
                .unwrap(),
            24,
            "2048",
        );

        assert_eq!(
            invoke(integerp, &[d12(7)], &env, Span::default())
                .unwrap()
                .unwrap()
                .as_predicate_bit(),
            Some(true),
        );
        let fraction = crate::domain_numeric::compute("/", &d12(1), &d12(2))
            .expect("D12 division produces exact ratio");
        assert!(matches!(fraction, Value::NumericComposition(_)));
        assert_eq!(
            invoke(integerp, &[fraction], &env, Span::default())
                .unwrap()
                .unwrap()
                .as_predicate_bit(),
            Some(false),
        );
    }

    #[test]
    fn add1_widens_signed_d24_and_sub1_returns_twos_complement_word() {
        let env = Environment::root();
        let add1 = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b001110).unwrap(),
        ));
        let sub1 = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b001111).unwrap(),
        ));

        // D24 max-positive + 1 widens; all-ones is now D24(-1), not a maximum.
        let carried = invoke(add1, &[d24((1 << 23) - 1)], &env, Span::default())
            .unwrap()
            .unwrap();
        let Value::BinaryNumber(ref number) = carried else {
            panic!("D24 carry must stay an exact numeric domain word");
        };
        assert_eq!(number.numeric_domain_width(), Some(48));
        let mut next_bits = vec![0; 48];
        next_bits[24] = 1; // full-width D48 encoding of 2^23
        assert_eq!(number.exact_numeric_domain_bits().unwrap(), next_bits);

        // After a D24 carry, ADD1 must continue in the new exact D48 domain.
        // The successor must not become a source literal, wrap, or stall.
        let resumed = invoke(add1, std::slice::from_ref(&carried), &env, Span::default())
            .unwrap()
            .unwrap();
        let Value::BinaryNumber(ref resumed_number) = resumed else {
            panic!("D48 ADD1 after carry must remain a numeric-domain value");
        };
        assert_eq!(resumed_number.numeric_domain_width(), Some(48));
        let mut advanced_bits = next_bits.clone();
        advanced_bits[47] = 1; // 2^23 + 1, not a D24 or unqualified literal
        assert_eq!(
            resumed_number.exact_numeric_domain_bits().unwrap(),
            advanced_bits
        );

        // 0 - 1 is the ordinary D24 two's-complement word for -1.
        let negative = invoke(sub1, &[d24(0)], &env, Span::default())
            .unwrap()
            .unwrap();
        let Value::BinaryNumber(ref negative_word) = negative else {
            panic!("D24 SUB1 below zero must return a signed D24 word");
        };
        assert_eq!(negative_word.numeric_domain_width(), Some(24));
        assert_eq!(negative.to_string(), "-1");
        assert_eq!(
            invoke(add1, &[negative], &env, Span::default())
                .unwrap()
                .unwrap(),
            d24(0),
        );
    }

    #[test]
    fn neg_reuses_exact_d5_difference_and_keeps_d24_boundaries() {
        let env = Environment::root();
        let neg = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b010010).unwrap(),
        ));
        for (operand, expected) in [(d24(0), d24(0)), (d24(7), d24(-7)), (d24(-7), d24(7))] {
            assert_eq!(
                invoke(neg, &[operand], &env, Span::default())
                    .unwrap()
                    .unwrap(),
                expected
            );
        }
        let widened = invoke(neg, &[d24(-(1 << 23))], &env, Span::default())
            .unwrap()
            .unwrap();
        let Value::BinaryNumber(ref number) = widened else {
            panic!("D24 minimum negation must remain a precise word");
        };
        assert_eq!(number.numeric_domain_width(), Some(48));
        assert_eq!(widened.to_string(), "8388608");

        for invalid in [Value::Nil, Value::Rational(crate::Rational::integer(7))] {
            assert_eq!(
                invoke(neg, &[invalid], &env, Span::default())
                    .unwrap()
                    .unwrap_err()
                    .kind,
                ErrorKind::Type
            );
        }
        for arguments in [vec![], vec![d24(1), d24(2)]] {
            assert_eq!(
                invoke(neg, &arguments, &env, Span::default())
                    .unwrap()
                    .unwrap_err()
                    .kind,
                ErrorKind::Arity
            );
        }
    }

    #[test]
    fn integerp_uses_exact_d24_identity_not_historical_q2_text() {
        let env = Environment::root();
        let integerp = CoreDomainIdentity::D6(crate::CoreD6::from_word(
            crate::Bit6::new(0b111110).unwrap(),
        ));
        let fraction = crate::domain_numeric::compute("/", &d24(7), &d24(2))
            .expect("D5 yields an exact noninteger fraction");
        assert!(matches!(fraction, Value::NumericComposition(_)));
        for (input, expected) in [
            (d24(7), true),
            (d24(-7), true),
            (d24(0), true),
            (fraction, false),
            (Value::String(std::rc::Rc::from("7")), false),
            (Value::String(std::rc::Rc::from("#q2:111/1")), false),
            (Value::Nil, false),
            (Value::Rational(crate::Rational::integer(7)), false),
        ] {
            let output = invoke(integerp, &[input], &env, Span::default())
                .expect("D6 INTEGERP resident")
                .expect("D6 INTEGERP executes");
            assert_eq!(output.as_predicate_bit(), Some(expected));
        }
        assert_eq!(
            invoke(integerp, &[], &env, Span::default())
                .unwrap()
                .unwrap_err()
                .kind,
            ErrorKind::Arity
        );
    }

    #[test]
    fn add1_sub1_use_same_d24_numeric_domain_not_legacy_one() {
        let env = Environment::root();
        for (bits, expected) in [(0b001110, d24(8)), (0b001111, d24(6))] {
            let identity =
                CoreDomainIdentity::D6(crate::CoreD6::from_word(crate::Bit6::new(bits).unwrap()));
            let actual = invoke(identity, &[d24(7)], &env, Span::default())
                .unwrap()
                .unwrap();
            assert_eq!(actual, expected);
            let blocked = invoke(
                identity,
                &[Value::Rational(crate::Rational::integer(7))],
                &env,
                Span::default(),
            )
            .unwrap()
            .unwrap_err();
            assert_eq!(blocked.kind, ErrorKind::Type);
        }
    }
}
