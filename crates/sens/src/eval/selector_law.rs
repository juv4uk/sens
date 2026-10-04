//! Production mechanism for the ratified CAR/CDR selector generator law.
//!
//! Semantic authority: #1961/#1975/#2055.
//!
//! A selector descendant is not looked up in a flat function table.
//! Its exact Core identity is decoded as:
//!
//! - D3 root 100 -> CAR
//! - D3 root 011 -> CDR
//! - every suffix bit 0 -> compose CAR
//! - every suffix bit 1 -> compose CDR
//!
//! The operation sequence is encoded outer-to-inner, so execution applies it
//! in reverse order to the argument value.

use super::special_forms;
use crate::{CoreDomainIdentity, ErrorKind, LanguageError, Span, Value};

const MAX_SELECTOR_DEPTH: usize = 6;

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
    // D7 is the ratified Sound7/Text7 domain, not selector geometry.
    // D8 re-enters the selector lineage only under the admitted root+suffix law.
    if !((3..=6).contains(&width) || width == 8) {
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

    let mut index = 0usize;
    while index < suffix_len {
        let shift = suffix_len - 1 - index;
        steps[index + 1] = if ((payload >> shift) & 1) == 0 {
            Step::Car
        } else {
            Step::Cdr
        };
        index += 1;
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
    fn selector_family_is_decoded_from_root_plus_suffix_only() {
        assert_eq!(decode(d3(0b100)).unwrap().len, 1);
        assert_eq!(decode(d3(0b011)).unwrap().len, 1);

        assert_eq!(
            decode(d4(0b1001)).unwrap().steps[..2],
            [Step::Car, Step::Cdr]
        );
        assert_eq!(
            decode(d5(0b01110)).unwrap().steps[..3],
            [Step::Cdr, Step::Cdr, Step::Car]
        );
        assert_eq!(
            decode(d6(0b100101)).unwrap().steps[..4],
            [Step::Car, Step::Cdr, Step::Car, Step::Cdr]
        );
        assert_eq!(
            decode(d8(0b10010101)).unwrap().steps[..6],
            [Step::Car, Step::Cdr, Step::Car, Step::Cdr, Step::Car, Step::Cdr]
        );
    }

    #[test]
    fn non_selector_words_are_not_minted_by_geometry() {
        for identity in [
            d3(0b001),
            d3(0b101),
            d4(0b0010),
            d5(0b01010),
            d6(0b010111),
        ] {
            assert_eq!(decode(identity), None);
        }
    }

    #[test]
    fn d3_through_d6_selectors_execute_without_descendant_rows() {
        let leaf = |n| Value::Number(n, crate::Exactness::Exact);

        // x = (((1 . 2) . (3 . 4)) . ((5 . 6) . (7 . 8)))
        let x = pair(
            pair(pair(leaf(1.0), leaf(2.0)), pair(leaf(3.0), leaf(4.0))),
            pair(pair(leaf(5.0), leaf(6.0)), pair(leaf(7.0), leaf(8.0))),
        );
        let span = Span { start: 0, end: 0 };

        // CAR
        assert_eq!(
            invoke(d3(0b100), std::slice::from_ref(&x), span).unwrap().unwrap(),
            pair(pair(leaf(1.0), leaf(2.0)), pair(leaf(3.0), leaf(4.0)))
        );
        // CADR = CAR(CDR(x))
        assert_eq!(
            invoke(d4(0b1001), &[proper([leaf(10.0), leaf(20.0)])], span)
                .unwrap()
                .unwrap(),
            leaf(20.0)
        );
        // CAAAR = CAR(CAR(CAR(x)))
        assert_eq!(
            invoke(d5(0b10000), std::slice::from_ref(&x), span).unwrap().unwrap(),
            leaf(1.0)
        );
        // CAAAAR = CAR(CAR(CAR(CAR(x2))))
        let x2 = pair(x.clone(), Value::Nil);
        assert_eq!(
            invoke(d6(0b100000), &[x2], span).unwrap().unwrap(),
            leaf(1.0)
        );

        // D8 10000000 = six CAR applications under the same admitted law.
        let mut x8 = leaf(9.0);
        for _ in 0..6 {
            x8 = pair(x8, Value::Nil);
        }
        assert_eq!(
            invoke(d8(0b10000000), &[x8], span).unwrap().unwrap(),
            leaf(9.0)
        );
    }

    #[test]
    fn ratified_d3_complement_preserves_selector_duality_through_d6() {
        // Under #3202, CAR=100 and CDR=011 are exact 3-bit complements.
        // Extending a selector path and flipping every bit must produce the
        // semantic dual path inside this proved selector family.
        for width in 3usize..=6 {
            let suffix_len = width - 3;
            let limit = 1u8 << suffix_len;
            for suffix in 0u8..limit {
                let car_word = (0b100u8 << suffix_len) | suffix;
                let mask = (1u8 << width) - 1;
                let dual_word = car_word ^ mask;

                let left = match width {
                    3 => decode(d3(car_word)),
                    4 => decode(d4(car_word)),
                    5 => decode(d5(car_word)),
                    6 => decode(d6(car_word)),
                    _ => unreachable!(),
                }
                .unwrap();

                let right = match width {
                    3 => decode(d3(dual_word)),
                    4 => decode(d4(dual_word)),
                    5 => decode(d5(dual_word)),
                    6 => decode(d6(dual_word)),
                    _ => unreachable!(),
                }
                .unwrap();

                assert_eq!(left.len, right.len);
                for index in 0..left.len {
                    assert_ne!(left.steps[index], right.steps[index]);
                }
            }
        }
    }

    #[test]
    fn one_root_law_generates_the_complete_bounded_selector_family() {
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
        for raw in 0u8..64 {
            generated += usize::from(decode(d6(raw)).is_some());
        }
        for raw in 0u8..=255 {
            generated += usize::from(decode(d8(raw)).is_some());
        }

        // 2 roots + 4 D4 + 8 D5 + 16 D6 + 64 D8 descendants.
        // D7 contributes zero: it is governed by Sound7/Text7 law.
        assert_eq!(generated, 94);
    }
}
