use crate::{ErrorKind, Exactness, LanguageError, Span, Value};
use std::rc::Rc;

/// Minimal runtime bridge from an exact Unicode scalar value to the language's
/// immutable string representation. Unicode/UTF-8 decoding policy stays in
/// Lisp; this function only materializes one already-interpreted scalar.
pub(crate) fn codepoint_to_string_values(
    arguments: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() != 1 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "codepoint->string expects exactly 1 argument(s)",
            span,
        ));
    }
    let scalar = exact_scalar_value(&arguments[0], span)?;
    let character = char::from_u32(scalar).ok_or_else(|| {
        LanguageError::new(
            ErrorKind::Type,
            "codepoint->string expects a Unicode scalar value · codepoint->string ochikuie skaliarne znachennia Unicode · codepoint->string erwartet einen Unicode-Skalarwert",
            span,
        )
    })?;
    Ok(Value::String(Rc::from(character.to_string().as_str())))
}

/// Minimal inverse bridge for UTF-8 encoding owned by Lisp. The runtime only
/// exposes the scalar value of exactly one already-materialized character;
/// byte encoding, validation policy, and transport meaning remain in Lisp.
pub(crate) fn string_to_codepoint_values(
    arguments: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() != 1 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "string->codepoint expects exactly 1 argument(s)",
            span,
        ));
    }
    let Value::String(text) = &arguments[0] else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "string->codepoint expects a one-character string · string->codepoint ochikuie riadok z odnoho symvolu · string->codepoint erwartet eine Zeichenkette mit genau einem Zeichen",
            span,
        ));
    };

    let mut characters = text.chars();
    let Some(character) = characters.next() else {
        return Err(invalid_character_string(span));
    };
    if characters.next().is_some() {
        return Err(invalid_character_string(span));
    }

    // The lower scalar extraction bridge retains its historical value shape.
    // Only the already admitted D8:11100000 CHAR-CODE caller in canon.rs
    // explicitly constructs a D24 numeric-domain result.
    Ok(Value::Number(character as u32 as f64, Exactness::Exact))
}

fn exact_scalar_value(value: &Value, span: Span) -> Result<u32, LanguageError> {
    let integer = match value {
        // Canonical result of D8:11100000 CHAR-CODE, exact-width D24.
        Value::BinaryNumber(bits) if bits.numeric_domain_width() == Some(24) => bits
            .as_bits()
            .iter()
            .fold(0u32, |scalar, &bit| (scalar << 1) | u32::from(bit)),
        Value::Number(number, Exactness::Exact) if number.is_finite() && number.fract() == 0.0 => {
            if *number < 0.0 || *number > 0x10ffff as f64 {
                return Err(invalid_scalar(span));
            }
            *number as u32
        }
        Value::Rational(rational) if rational.is_integer() => {
            let number = rational
                .as_precise_i64()
                .ok_or_else(|| invalid_scalar(span))?;
            u32::try_from(number).map_err(|_| invalid_scalar(span))?
        }
        _ => return Err(invalid_scalar(span)),
    };

    if integer > 0x10ffff || (0xd800..=0xdfff).contains(&integer) {
        return Err(invalid_scalar(span));
    }
    Ok(integer)
}

fn invalid_scalar(span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::Type,
        "codepoint->string expects an exact Unicode scalar integer (0..0x10FFFF excluding surrogates) · codepoint->string ochikuie tochne tsile skaliarne znachennia Unicode · codepoint->string erwartet eine exakte Unicode-Skalarzahl",
        span,
    )
}

fn invalid_character_string(span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::Type,
        "string->codepoint expects exactly one Unicode scalar character · string->codepoint ochikuie rivno odyn skaliarnyi symvol Unicode · string->codepoint erwartet genau ein Unicode-Skalarzeichen",
        span,
    )
}

#[cfg(test)]
mod exact_d24_char_code_tests {
    use super::*;
    use crate::BinaryNumber;

    #[test]
    fn scalar_bridge_preserves_legacy_shape_and_accepts_exact_d24_inverse() {
        for source in ["a", "ї", "𐐷"] {
            let observed =
                string_to_codepoint_values(&[Value::String(Rc::from(source))], Span::default())
                    .expect("one Unicode scalar is admissible");
            assert!(
                matches!(&observed, Value::Number(_, Exactness::Exact)),
                "lower bridge must leave explicit D24 qualification to D8 CHAR-CODE"
            );
            let scalar = u32::from(source.chars().next().expect("one scalar"));
            let bits = (0u32..24)
                .rev()
                .map(|shift| ((scalar >> shift) & 1) as u8)
                .collect::<Vec<_>>();
            let qualified = BinaryNumber::from_numeric_domain_bits(24, &bits)
                .expect("Unicode scalar admits a D24 carrier");
            let back =
                codepoint_to_string_values(&[Value::BinaryNumber(qualified)], Span::default())
                    .expect("explicit exact D24 scalar round-trips");
            assert!(matches!(&back, Value::String(value) if value.as_ref() == source));
        }
    }

    #[test]
    fn char_code_rejects_non_scalar_strings() {
        for source in ["", "ab"] {
            let result =
                string_to_codepoint_values(&[Value::String(Rc::from(source))], Span::default());
            assert!(result.is_err());
        }
    }

    #[test]
    fn code_char_rejects_surrogate_even_when_d24_qualified() {
        let bits = (0u32..24)
            .rev()
            .map(|shift| ((0xd800u32 >> shift) & 1) as u8)
            .collect::<Vec<_>>();
        let qualified = BinaryNumber::from_numeric_domain_bits(24, &bits)
            .expect("the carrier exists but is not a Unicode scalar");
        let result = codepoint_to_string_values(&[Value::BinaryNumber(qualified)], Span::default());
        assert!(result.is_err());
    }
}
