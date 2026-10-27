//! Production mechanism for the ratified CAR/CDR selector generator law.
//!
//! Semantic authority: #3202 / #2055.
//!
//! One recursive law for ratified selector-family residents in D3-D6, D8-D10.
//! D3 roots 100 (CAR) and 011 (CDR); each appended 0 means compose
//! CAR inside the parent, and each appended 1 means compose CDR.
//! D7 is keyboard data, never a selector rung. The D8-D10 residents already
//! have these exact family coordinates in the owner-ratified domain tables.
//! Neither occupancy outside these two prefix families nor future D11 proposals
//! acquires a callable mechanism from this law.
//!
//! This law is family-local. It does not create a universal suffix meaning.
//! D7 and widths outside the ratified family fail closed.

use super::special_forms;
use crate::{DomainIdentity, ErrorKind, LanguageError, Span, Value};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Step {
    Car,
    Cdr,
}

/// Decode only the exact-width, ratified selector shape. No temporary
/// instruction array: the suffix bits already encode the execution order.
fn decode(identity: DomainIdentity) -> Option<(Step, u16, usize)> {
    let width = identity.width();
    // W7 belongs to D7 text; W11 is research only. Nothing is inferred
    // about other domain families merely from suffix similarity.
    if !matches!(width, 3..=6 | 8..=10) {
        return None;
    }

    let payload = identity.packed_bits();
    let root = match payload >> (width - 3) {
        0b100 => Step::Car,
        0b011 => Step::Cdr,
        _ => return None,
    };
    Some((root, payload, width - 3))
}

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

pub(super) fn invoke(
    identity: DomainIdentity,
    args: &[Value],
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let (root, payload, suffix_len) = decode(identity)?;

    if args.len() != 1 {
        return Some(Err(LanguageError::new(
            ErrorKind::Arity,
            format!(
                "{identity}: exact selector law expects 1 argument; received {}",
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
