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
