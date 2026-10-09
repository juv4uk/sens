//! Production mechanism for the ratified CAR/CDR selector generator law.
//!
//! Semantic authority: #3202 / #2055.
//!
//! Current proved family:
//! - D3 root 100 -> CAR
//! - D3 root 011 -> CDR
//! - selector-family suffix 0 -> compose CAR
//! - selector-family suffix 1 -> compose CDR
//! - D4 admits one selector suffix bit
//! - owner-ratified D5 v2 (#3305/#3331) admits two selector suffix bits
//! - owner-ratified D6 (#3393) admits three selector suffix bits
//!
//! This law is family-local. It does not create a universal suffix meaning.
//! D7/D8 remain outside this production selector decoder and fail closed.

use super::special_forms;
use crate::{CoreDomainIdentity, ErrorKind, LanguageError, Span, Value};

const MAX_SELECTOR_DEPTH: usize = 4;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Step {
    Car,
    Cdr,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct SelectorProgram {
    steps: [Step; MAX_SELECTOR_DEPTH],
    len: usize,
}

fn decode(identity: CoreDomainIdentity) -> Option<SelectorProgram> {
    let width = identity.width();
    if !(3..=6).contains(&width) {
        return None;
    }

    let payload = identity.packed_bits();
    let prefix = payload >> (width - 3);
    let root = match prefix {
        0b100 => Step::Car,
        0b011 => Step::Cdr,
        _ => return None,
    };

    let suffix_len = width - 3;
    let mut steps = [Step::Car; MAX_SELECTOR_DEPTH];
    steps[0] = root;

    for index in 0..suffix_len {
        let shift = suffix_len - 1 - index;
        steps[index + 1] = if ((payload >> shift) & 1) == 0 {
            Step::Car
        } else {
            Step::Cdr
        };
    }

    Some(SelectorProgram {
        steps,
        len: 1 + suffix_len,
    })
}

pub(crate) fn compiler_execution_role(
    identity: CoreDomainIdentity,
) -> Option<crate::compiler_role::CompilerExecutionRole> {
    // The compiler role is a projection of the same production selector
    // decoder used by evaluator execution, never a second bits-to-role table.
    // The first compiler bridge admits only the D3 root itself; D4/D5
    // descendants have longer selector programs and therefore stay outside
    // this bounded slice.
    if identity.width() != 3 {
        return None;
    }
    let program = decode(identity)?;
    if program.len != 1 {
        return None;
    }
    match program.steps[0] {
        Step::Car => Some(crate::compiler_role::CompilerExecutionRole::SelectorHead),
        Step::Cdr => Some(crate::compiler_role::CompilerExecutionRole::SelectorTail),
    }
}

pub(super) fn invoke(
    identity: CoreDomainIdentity,
    args: &[Value],
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let program = decode(identity)?;

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

    let mut value = args[0].clone();
    for step in program.steps[..program.len].iter().rev() {
        value = match step {
            Step::Car => match special_forms::car_value(&value, span) {
                Ok(value) => value,
                Err(error) => return Some(Err(error)),
            },
            Step::Cdr => match special_forms::cdr_value(&value, span) {
                Ok(value) => value,
                Err(error) => return Some(Err(error)),
            },
        };
    }

    Some(Ok(value))
}
