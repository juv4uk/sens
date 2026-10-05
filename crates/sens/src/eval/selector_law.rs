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
//! Current D7 remains outside this callable selector decoder by its Sound/Text role; D8 remains research. Both fail closed here.

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

pub(super) fn has_mechanism(identity: CoreDomainIdentity) -> bool {
    decode(identity).is_some()
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
    use crate::{Bija3, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, CoreD4, CoreD5, CoreD6, CoreD8, DomainIdentity, SoundD7};
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
    fn selector_family_is_decoded_from_ratified_roots_and_selector_suffixes() {
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

        let expected = [
            (0b100000, [Step::Car, Step::Car, Step::Car, Step::Car]),
            (0b100001, [Step::Car, Step::Car, Step::Car, Step::Cdr]),
            (0b100010, [Step::Car, Step::Car, Step::Cdr, Step::Car]),
            (0b100011, [Step::Car, Step::Car, Step::Cdr, Step::Cdr]),
            (0b100100, [Step::Car, Step::Cdr, Step::Car, Step::Car]),
            (0b100101, [Step::Car, Step::Cdr, Step::Car, Step::Cdr]),
            (0b100110, [Step::Car, Step::Cdr, Step::Cdr, Step::Car]),
            (0b100111, [Step::Car, Step::Cdr, Step::Cdr, Step::Cdr]),
            (0b011000, [Step::Cdr, Step::Car, Step::Car, Step::Car]),
            (0b011001, [Step::Cdr, Step::Car, Step::Car, Step::Cdr]),
            (0b011010, [Step::Cdr, Step::Car, Step::Cdr, Step::Car]),
            (0b011011, [Step::Cdr, Step::Car, Step::Cdr, Step::Cdr]),
            (0b011100, [Step::Cdr, Step::Cdr, Step::Car, Step::Car]),
            (0b011101, [Step::Cdr, Step::Cdr, Step::Car, Step::Cdr]),
            (0b011110, [Step::Cdr, Step::Cdr, Step::Cdr, Step::Car]),
            (0b011111, [Step::Cdr, Step::Cdr, Step::Cdr, Step::Cdr]),
        ];
        for (raw, steps) in expected {
            assert_eq!(decode(d6(raw)).unwrap().steps[..4], steps);
        }
    }

    #[test]
    fn old_roots_and_higher_width_prefix_collisions_fail_closed() {
        for identity in [
            d3(0b101),
            d3(0b110),
            d4(0b1010),
            d4(0b1011),
            d4(0b1100),
            d4(0b1101),
            d5(0b10100), // REVERSE, not a selector
            d5(0b11101), // MEMBER, not a selector
            d6(0b101000), // MAP, not a selector
            d8(0b011000), // same payload as D6 CDAAAR, wrong domain/width
            d8(0b10000000),
        ] {
            assert_eq!(decode(identity), None);
        }

        let d7_identity: DomainIdentity =
            SoundD7::from_word(Bit7::new(0b011000).unwrap()).into();
        assert_eq!(
            d7_identity.core_operation(),
            None,
            "same payload in current non-callable D7 must never enter the callable D6 selector decoder"
        );
    }

    #[test]
    fn d3_through_d6_selectors_execute_without_descendant_rows() {
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

        assert_eq!(invoke(d5(0b10000), std::slice::from_ref(&x), span).unwrap().unwrap(), leaf(1.0)); // CAAAR
        assert_eq!(invoke(d5(0b10001), std::slice::from_ref(&x), span).unwrap().unwrap(), leaf(5.0)); // CAADR
        assert_eq!(invoke(d5(0b10010), std::slice::from_ref(&x), span).unwrap().unwrap(), leaf(3.0)); // CADAR
        assert_eq!(invoke(d5(0b10011), std::slice::from_ref(&x), span).unwrap().unwrap(), leaf(7.0)); // CADDR
        assert_eq!(invoke(d5(0b01100), std::slice::from_ref(&x), span).unwrap().unwrap(), leaf(2.0)); // CDAAR
        assert_eq!(invoke(d5(0b01101), std::slice::from_ref(&x), span).unwrap().unwrap(), leaf(6.0)); // CDADR
        assert_eq!(invoke(d5(0b01110), std::slice::from_ref(&x), span).unwrap().unwrap(), leaf(4.0)); // CDDAR
        assert_eq!(invoke(d5(0b01111), &[x], span).unwrap().unwrap(), leaf(8.0)); // CDDDR

        let y = pair(
            pair(
                pair(pair(leaf(1.0), leaf(2.0)), pair(leaf(3.0), leaf(4.0))),
                pair(pair(leaf(5.0), leaf(6.0)), pair(leaf(7.0), leaf(8.0))),
            ),
            pair(
                pair(pair(leaf(9.0), leaf(10.0)), pair(leaf(11.0), leaf(12.0))),
                pair(pair(leaf(13.0), leaf(14.0)), pair(leaf(15.0), leaf(16.0))),
            ),
        );

        for (raw, expected) in [
            (0b100000, 1.0), (0b100001, 9.0), (0b100010, 5.0), (0b100011, 13.0),
            (0b100100, 3.0), (0b100101, 11.0), (0b100110, 7.0), (0b100111, 15.0),
            (0b011000, 2.0), (0b011001, 10.0), (0b011010, 6.0), (0b011011, 14.0),
            (0b011100, 4.0), (0b011101, 12.0), (0b011110, 8.0), (0b011111, 16.0),
        ] {
            assert_eq!(
                invoke(d6(raw), std::slice::from_ref(&y), span).unwrap().unwrap(),
                leaf(expected),
                "D6 selector {raw:06b}"
            );
        }
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
    fn complement_commutes_with_selector_growth_through_d6() {
        // #3499/#3506: a proved family law lifts across width only where the
        // same semantic child generator is admitted:
        //
        // C_{n+1}(G_b(p)) = G_{1-b}(C_n(p)).
        //
        // Check both coordinate complement and independently decoded CAR/CDR
        // step complement. This is family-local evidence, never a global
        // antipodal law for all residents of D4/D5/D6.
        let assert_stepwise_complements = |left: CoreDomainIdentity, right: CoreDomainIdentity| {
            let a = decode(left).expect("left selector");
            let b = decode(right).expect("right selector");
            assert_eq!(a.len, b.len);
            for index in 0..a.len {
                assert_ne!(a.steps[index], b.steps[index]);
            }
        };

        for parent in [0b100u8, 0b011u8] {
            let parent_dual = parent ^ 0b111;
            assert_stepwise_complements(d3(parent), d3(parent_dual));
            for child_bit in [0u8, 1u8] {
                let child = (parent << 1) | child_bit;
                let expected_dual = (parent_dual << 1) | (1 - child_bit);
                assert_eq!(child ^ 0b1111, expected_dual);
                assert_stepwise_complements(d4(child), d4(expected_dual));
            }
        }

        for parent in [0b1000u8, 0b1001u8, 0b0110u8, 0b0111u8] {
            let parent_dual = parent ^ 0b1111;
            assert_stepwise_complements(d4(parent), d4(parent_dual));
            for child_bit in [0u8, 1u8] {
                let child = (parent << 1) | child_bit;
                let expected_dual = (parent_dual << 1) | (1 - child_bit);
                assert_eq!(child ^ 0b1_1111, expected_dual);
                assert_stepwise_complements(d5(child), d5(expected_dual));
            }
        }

        for parent in [
            0b10000u8, 0b10001u8, 0b10010u8, 0b10011u8,
            0b01100u8, 0b01101u8, 0b01110u8, 0b01111u8,
        ] {
            let parent_dual = parent ^ 0b1_1111;
            assert_stepwise_complements(d5(parent), d5(parent_dual));
            for child_bit in [0u8, 1u8] {
                let child = (parent << 1) | child_bit;
                let expected_dual = (parent_dual << 1) | (1 - child_bit);
                assert_eq!(child ^ 0b11_1111, expected_dual);
                assert_stepwise_complements(d6(child), d6(expected_dual));
            }
        }
    }

    #[test]
    fn exactly_two_d3_four_d4_eight_d5_and_sixteen_d6_selectors_are_admitted() {
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
        assert_eq!(generated, 30);
    }
}
