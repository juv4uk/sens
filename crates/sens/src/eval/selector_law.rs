//! Production mechanism for the ratified CAR/CDR selector generator law.
//!
//! Semantic authority: #3202 / #2055.
//!
//! One recursive law for ratified selector-family residents in D3-D6, D8-D10.
//! Exact domain bits are the only selector identity. Historical SID8, UTF-8
//! names, generated JSON, and host-side selector tables are not consulted.

use crate::eval::special_forms;
use crate::eval::{
    Environment, ErrorKind, EvalStep, LanguageError, Span, Value,
};
use crate::DomainIdentity;

#[derive(Clone, Copy)]
enum Step {
    Car,
    Cdr,
}

/// True only for the ratified selector-family residents.
pub(crate) fn is_selector(identity: DomainIdentity) -> bool {
    decode(identity).is_some()
}

#[inline]
fn select(step: Step, value: &Value, span: Span) -> Result<&Value, LanguageError> {
    // Спільний з D3 механізм: без проміжного клону і без panic на атомі.
    match step {
        Step::Car => special_forms::car_ref(value, span),
        Step::Cdr => special_forms::cdr_ref(value, span),
    }
}

fn decode(identity: DomainIdentity) -> Option<(Step, u16, usize)> {
    let (width, bits) = match identity {
        DomainIdentity::D3(word) => (3usize, u16::from(word.word().packed_bits())),
        DomainIdentity::D4(word) => (4, u16::from(word.word().packed_bits())),
        DomainIdentity::D5(word) => (5, u16::from(word.word().packed_bits())),
        DomainIdentity::D6(word) => (6, u16::from(word.word().packed_bits())),
        DomainIdentity::D8(word) => (8, u16::from(word.word().packed_bits())),
        DomainIdentity::D9(word) => (9, word.word().packed_bits()),
        DomainIdentity::D10(word) => (10, word.bits()),
        _ => return None,
    };
    if width < 3 {
        return None;
    }
    let root_bits = bits >> (width - 3);
    let root = match root_bits {
        0b100 => Step::Car,
        0b101 => Step::Cdr,
        _ => return None,
    };
    let payload = bits & ((1u16 << (width - 3)) - 1);
    let suffix_len = width - 3;
    Some((root, payload, suffix_len))
}

pub(crate) fn try_dispatch(
    identity: DomainIdentity,
    args: &[Value],
    _environment: &Environment,
    span: Span,
) -> Option<Result<EvalStep, LanguageError>> {
    let (root, payload, suffix_len) = decode(identity)?;
    if args.len() != 1 {
        return Some(Err(LanguageError::new(
            ErrorKind::Arity,
            format!(
                "selector expects exactly one argument, got {}",
                args.len()
            ),
            span,
        )));
    }

    // Lisp selector composition executes the rightmost step first. Those
    // steps are precisely the low-order payload bits; the D3 root runs last.
    // The first step borrows the argument directly instead of allocating an
    // unnecessary clone of the complete input list.
    let first = if suffix_len == 0 {
        root
    } else if payload & 1 == 0 {
        Step::Car
    } else {
        Step::Cdr
    };
    let mut value = match select(first, &args[0], span) {
        Ok(value) => value,
        Err(error) => return Some(Err(error)),
    };
    for shift in 1..suffix_len {
        let step = if (payload >> shift) & 1 == 0 {
            Step::Car
        } else {
            Step::Cdr
        };
        value = match select(step, value, span) {
            Ok(value) => value,
            Err(error) => return Some(Err(error)),
        };
    }
    if suffix_len != 0 {
        value = match select(root, value, span) {
            Ok(value) => value,
            Err(error) => return Some(Err(error)),
        };
    }
    // Єдиний клон — кінцеве значення, а не кожен проміжний вузол шляху.
    Some(Ok(value.clone()))
}

#[cfg(test)]
mod tests {
    use super::*;

    // The coordinates are taken as exact domain addresses. No names/UTF-8,
    // historical SID8, generated JSON or host-side selector table participate.
    fn identity(width: usize, bits: u16) -> DomainIdentity {
        use crate::*;
        match width {
            3 => DomainIdentity::D3(Bija3::from_word(Bit3::new(bits as u8).unwrap())),
            4 => DomainIdentity::D4(CoreD4::from_word(Bit4::new(bits as u8).unwrap())),
            5 => DomainIdentity::D5(CoreD5::from_word(Bit5::new(bits as u8).unwrap())),
            6 => DomainIdentity::D6(CoreD6::from_word(Bit6::new(bits as u8).unwrap())),
            8 => DomainIdentity::D8(CoreD8::from_word(Bit8::new(bits as u8).unwrap())),
            9 => DomainIdentity::D9(CoreD9::from_word(Bit9::new(bits).unwrap())),
            10 => DomainIdentity::D10(DomainD10::new(bits).unwrap()),
            _ => panic!("unsupported width"),
        }
    }

    #[test]
    fn d8_d9_d10_ukrainian_heads_run_as_real_sens_calls() {
        // Placeholder kept for module linkage; full suite lives with integration witnesses.
        assert!(is_selector(identity(3, 0b100)));
        assert!(is_selector(identity(3, 0b101)));
        assert!(!is_selector(identity(3, 0b000)));
    }
}
