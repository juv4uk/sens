//! Quarantined compatibility primitive dispatch.
//!
//! This module is intentionally byte-shaped and contains no exact-domain
//! identity types. Canonical domain execution lives in eval/canon.rs and the
//! domain-law modules. Rows disappear from here as mechanisms migrate.

use super::{arithmetic, builtins, special_forms};
use crate::{Environment, LanguageError, Sens8, Span, Value};

type PrimitiveFn = fn(&[Value], &Environment, Span) -> Result<Value, LanguageError>;

fn exact_args(
    sid: Sens8,
    args: &[Value],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if args.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        crate::ErrorKind::Arity,
        format!(
            "{sid}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            args.len()
        ),
        span,
    ))
}

fn prim_numeric_equal(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    arithmetic::comparison_on_values("=", args, span)
}

fn prim_eval(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args(crate::sens!(01001101), args, 1, span)?;
    special_forms::eval_values(args, env, span)
}

fn primitive(sid: Sens8) -> Option<PrimitiveFn> {
    match sid.packed_byte() {
        0b0001_1100 => Some(prim_numeric_equal),
        0b0100_1101 => Some(prim_eval),
        0b0011_1011 => Some(builtins::prim_00111011),
        0b0011_1100 => Some(builtins::prim_00111100),
        0b0011_1101 => Some(builtins::prim_00111101),
        0b0011_1110 => Some(builtins::prim_00111110),
        0b0101_0000 => Some(builtins::prim_01010000),
        0b0100_1111 => Some(builtins::prim_01001111),
        0b0101_1010 => Some(builtins::prim_01011010),
        0b0101_1011 => Some(builtins::prim_01011011),
        0b0101_1100 => Some(builtins::prim_01011100),
        0b0101_1101 => Some(builtins::prim_01011101),
        0b0101_0001 => Some(builtins::prim_01010001),
        0b0101_0010 => Some(builtins::prim_01010010),
        0b0101_0011 => Some(builtins::prim_01010011),
        0b0101_0100 => Some(builtins::prim_01010100),
        0b0101_0101 => Some(builtins::prim_01010101),
        0b0100_0001 => Some(builtins::prim_01000001),
        0b0011_1010 => Some(builtins::prim_00111010),
        0b0010_0100 => Some(builtins::prim_00100100),
        0b0100_0010 => Some(builtins::prim_01000010),
        0b0100_0011 => Some(builtins::prim_01000011),
        0b0011_1111 => Some(builtins::prim_00111111),
        0b0100_0000 => Some(builtins::prim_01000000),
        0b0100_0100 => Some(builtins::prim_01000100),
        0b0100_0101 => Some(builtins::prim_01000101),
        0b1010_0001 => Some(builtins::prim_10100001),
        0b1010_0000 => Some(builtins::prim_10100000),
        0b0100_1000 => Some(builtins::prim_01001000),
        0b0100_1001 => Some(builtins::prim_01001001),
        0b0100_1100 => Some(builtins::prim_01001100),
        0b0100_1010 => Some(builtins::prim_01001010),
        0b0100_1011 => Some(builtins::prim_01001011),
        0b0010_0110 => Some(builtins::prim_00100110),
        0b0101_0110 => Some(builtins::prim_01010110),
        0b0101_0111 => Some(builtins::prim_01010111),
        0b0101_1000 => Some(builtins::prim_01011000),
        0b0101_1001 => Some(builtins::prim_01011001),
        0b0100_1110 => Some(builtins::prim_01001110),
        _ => None,
    }
}

pub(super) fn invoke(
    sid: Sens8,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    primitive(sid).map(|function| function(args, environment, span))
}

pub(super) fn has(sid: Sens8) -> bool {
    primitive(sid).is_some()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn migrated_d3_d5_bytes_are_absent_from_quarantine() {
        for byte in [
            0b0000_0010, 0b0000_0011, 0b0000_0100, 0b0000_0101, 0b0000_0110,
            0b0000_1100, 0b0000_1101, 0b0000_1110, 0b0000_1111, 0b0001_1010,
            0b0001_1011,
        ] {
            assert!(!has(Sens8::from_packed_byte(byte)), "{byte:08b}");
        }
        assert!(has(Sens8::from_packed_byte(0b0100_1100)));
    }
}
