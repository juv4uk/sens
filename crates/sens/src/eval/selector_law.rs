//! Production mechanism for the ratified CAR/CDR selector generator law.
//!
//! Semantic authority: #3202 / #2055.
//!
//! Current proved family:
//! - D3 root 100 -> CAR
//! - D3 root 011 -> CDR
//! - each admitted selector suffix bit 0 -> compose CAR
//! - each admitted selector suffix bit 1 -> compose CDR
//! - Contract 11.3 admits exactly the D5 depth-3 descendants of the same law
//!
//! The proved production family is bounded to D3/D4/D5. D6+ ancestry is not
//! inferred from width or prefix shape and remains fail-closed under #3209.

use super::special_forms;
use crate::{CoreDomainIdentity, ErrorKind, LanguageError, Span, Value};

const MAX_SELECTOR_DEPTH: usize = 3;

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
    if !(3..=5).contains(&width) {
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

    for suffix_index in 0..suffix_len {
        let shift = suffix_len - 1 - suffix_index;
        steps[1 + suffix_index] = if ((payload >> shift) & 1) == 0 {
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Bit4, Bit5, Bit6, Bit8, CoreD4, CoreD5, CoreD6, CoreD8};
    use std::rc::Rc;

    fn pair(head: Value, tail: Value) -> Value {
        Value::Pair(Rc::new(head), Rc::new(tail))
    }

    fn proper(values: impl IntoIterator<Item = Value>) -> Value {
        let mut result = Value::Nil;
        let mut values = values.into_iter().collect::<Vec<_>>();
        while let Some(value) = values.pop() {
            result = pair(value, result);
        }
        result
    }

    fn d3(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()))
    }
    fn d4(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()))
    }
    fn d5(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(raw).unwrap()))
    }
    fn d6(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(raw).unwrap()))
    }
    fn d8(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(raw).unwrap()))
    }

    #[test]
    fn selector_family_is_decoded_from_root_plus_ratified_d4_d5_suffixes() {
        assert_eq!(decode(d3(0b100)).unwrap().steps[..1], [Step::Car]);
        assert_eq!(decode(d3(0b011)).unwrap().steps[..1], [Step::Cdr]);

        assert_eq!(decode(d4(0b1000)).unwrap().steps[..2], [Step::Car, Step::Car]);
        assert_eq!(decode(d4(0b1001)).unwrap().steps[..2], [Step::Car, Step::Cdr]);
        assert_eq!(decode(d4(0b0110)).unwrap().steps[..2], [Step::Cdr, Step::Car]);
        assert_eq!(decode(d4(0b0111)).unwrap().steps[..2], [Step::Cdr, Step::Cdr]);

        assert_eq!(decode(d5(0b10000)).unwrap().steps[..3], [Step::Car, Step::Car, Step::Car]);
        assert_eq!(decode(d5(0b10001)).unwrap().steps[..3], [Step::Car, Step::Car, Step::Cdr]);
        assert_eq!(decode(d5(0b10010)).unwrap().steps[..3], [Step::Car, Step::Cdr, Step::Car]);
        assert_eq!(decode(d5(0b10011)).unwrap().steps[..3], [Step::Car, Step::Cdr, Step::Cdr]);
        assert_eq!(decode(d5(0b01100)).unwrap().steps[..3], [Step::Cdr, Step::Car, Step::Car]);
        assert_eq!(decode(d5(0b01101)).unwrap().steps[..3], [Step::Cdr, Step::Car, Step::Cdr]);
        assert_eq!(decode(d5(0b01110)).unwrap().steps[..3], [Step::Cdr, Step::Cdr, Step::Car]);
        assert_eq!(decode(d5(0b01111)).unwrap().steps[..3], [Step::Cdr, Step::Cdr, Step::Cdr]);
    }

    #[test]
    fn old_roots_nonselector_d5_and_unratified_higher_widths_fail_closed() {
        for identity in [
            d3(0b101),
            d3(0b110),
            d4(0b1010),
            d4(0b1011),
            d4(0b1100),
            d4(0b1101),
            d5(0b10100), // REVERSE, not a selector
            d5(0b11101), // MEMBER, not a selector
            d6(0b100000),
            d8(0b10000000),
        ] {
            assert_eq!(decode(identity), None);
        }
    }

    #[test]
    fn d3_d4_d5_selectors_execute_without_descendant_tables() {
        let leaf = |n| Value::Number(n, crate::Exactness::Exact);
        let x = pair(
            pair(pair(leaf(1.0), leaf(2.0)), pair(leaf(3.0), leaf(4.0))),
            pair(pair(leaf(5.0), leaf(6.0)), pair(leaf(7.0), leaf(8.0))),
        );
        let span = Span { start: 0, end: 0 };

        assert_eq!(
            invoke(d3(0b100), std::slice::from_ref(&x), span).unwrap().unwrap(),
            pair(pair(leaf(1.0), leaf(2.0)), pair(leaf(3.0), leaf(4.0)))
        );
        assert_eq!(
            invoke(d3(0b011), std::slice::from_ref(&x), span).unwrap().unwrap(),
            pair(pair(leaf(5.0), leaf(6.0)), pair(leaf(7.0), leaf(8.0)))
        );
        assert_eq!(
            invoke(d4(0b1001), &[proper([leaf(10.0), leaf(20.0)])], span)
                .unwrap()
                .unwrap(),
            leaf(20.0)
        );

        let nested = proper([
            proper([
                proper([leaf(10.0), leaf(20.0)]),
                proper([leaf(30.0), leaf(40.0)]),
            ]),
            proper([
                proper([leaf(50.0), leaf(60.0)]),
                proper([leaf(70.0), leaf(80.0)]),
            ]),
        ]);
        assert_eq!(
            invoke(d5(0b10010), &[nested], span).unwrap().unwrap(),
            proper([leaf(30.0), leaf(40.0)])
        );
    }

    #[test]
    fn complement_pairs_flip_every_selector_step_inside_the_proved_d4_family() {
        for (left, right) in [(0b1000, 0b0111), (0b1001, 0b0110)] {
            let a = decode(d4(left)).unwrap();
            let b = decode(d4(right)).unwrap();
            assert_eq!(a.len, b.len);
            for index in 0..a.len {
                assert_ne!(a.steps[index], b.steps[index]);
            }
            assert_eq!(left ^ 0b1111, right);
        }
    }

    #[test]
    fn exactly_two_d3_four_d4_and_eight_d5_selectors_are_admitted() {
        let mut generated = 0usize;
        for raw in 0u8..8 {
            generated += usize::from(decode(d3(raw)).is_some());
        }
        for raw in 0u8..16 {
            generated += usize::from(decode(d4(raw)).is_some());
        }
        for raw in 0u8..32 {
            generated += usize::from(decode(d5(raw)).is_some());
        }
        assert_eq!(generated, 14);

        assert_eq!(decode(d6(0b100000)), None);
        assert_eq!(decode(d8(0b10000000)), None);
    }
}
