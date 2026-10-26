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
            _ => panic!("only ratified selector domains"),
        }
    }

    fn full_pair_tree(depth: usize, first: &mut usize) -> Value {
        if depth == 0 {
            let leaf = *first;
            *first += 1;
            return Value::Symbol(format!("листок-{leaf}").into());
        }
        Value::Pair(std::rc::Rc::new(crate::PairNode {
            head: full_pair_tree(depth - 1, first),
            tail: full_pair_tree(depth - 1, first),
        }))
    }

    #[test]
    fn one_suffix_law_generates_all_478_ratified_selectors_without_manual_definitions() {
        let mut count = 0;
        for width in [3usize, 4, 5, 6, 8, 9, 10] {
            let depth = width - 2;
            let mut leaf = 0;
            let input = full_pair_tree(depth, &mut leaf);
            for root in [0b011u16, 0b100] {
                for suffix in 0..(1u16 << (width - 3)) {
                    let bits = (root << (width - 3)) | suffix;
                    let key = identity(width, bits);
                    let result = invoke(key, &[input.clone()], Span::default())
                        .expect("all ratified selector addresses match the family law")
                        .expect("each selector is an executable CAR/CDR composition");
                    // Path order is suffix right-to-left, then D3 root.
                    // Suffix bits are applied inside first; the D3 root is last.
                    let mut digits: Vec<usize> = (0..width - 3)
                        .map(|i| usize::from((suffix >> i) & 1 != 0))
                        .collect();
                    digits.push(usize::from(root == 0b011));
                    let expected_leaf = digits.iter().fold(0usize, |acc, bit| 2 * acc + *bit);
                    assert_eq!(
                        result,
                        Value::Symbol(format!("листок-{expected_leaf}").into()),
                        "D{width}:{bits:0width$b} must obey right-to-left CAR/CDR composition",
                        width = width,
                    );
                    count += 1;
                }
            }
        }
        assert_eq!(count, 478);
    }

    #[test]
    fn one_d10_ukrainian_head_executes_without_a_handwritten_definition() {
        // Eight nested CONS pairs; the ratified D10:1000000000 selector
        // is CAR applied eight times. Source spelling comes only from the
        // canonical `укр` projection of its exact domain coordinate.
        let identity = identity(10, 0b1000000000);
        let name = crate::semantic_registry::selector_ukr_for_exact(identity)
            .expect("ratified D10 selector has an Ukrainian projection");
        assert_eq!(
            crate::semantic_registry::exact_uk_callable_for_source_head(name),
            Some(identity),
            "the current Ukrainian D10 spelling must invert to its exact coordinate"
        );
        let mut nested = "(як-є атом?)".to_owned();
        for _ in 0..8 {
            nested = format!("(сполучити {nested} (як-є ()))");
        }
        let mut session = crate::Session::default();
        let actual = crate::eval_program(&format!("({name} {nested})"), &mut session)
            .expect("SENS must execute a generated D10 CAR chain");
        let mut oracle = crate::Session::default();
        let expected =
            crate::eval_program("(як-є атом?)", &mut oracle).expect("ratified D3 quoted atom");
        assert_eq!(actual.value, expected.value);
    }

    #[test]
    fn ukrainian_selector_names_agree_with_ratified_tables() {
        // Both directions are checked against the *current* Lisp authority.
        // The table, rather than a Rust list of 448 definitions, owns names.
        let tables = [
            (8usize, include_str!("../../../../lib/domains/d8.lisp")),
            (9usize, include_str!("../../../../lib/domains/d9.lisp")),
            (10usize, include_str!("../../../../lib/domains/d10.lisp")),
        ];
        let mut witnessed = 0;
        for (width, table) in tables {
            for (root, prefix, ukrainian) in [(0b011u16, "р", "решта"), (0b100u16, "п", "перше")]
            {
                for suffix in 0..(1u16 << (width - 3)) {
                    let bits = (root << (width - 3)) | suffix;
                    let exact = identity(width, bits);
                    let mut small = prefix.to_owned();
                    let mut full = ukrainian.to_owned();
                    for shift in (0..width - 3).rev() {
                        let tail = (suffix >> shift) & 1 == 1;
                        small.push('-');
                        small.push(if tail { 'р' } else { 'п' });
                        full.push_str(if tail {
                            "-від-решта"
                        } else {
                            "-від-перше"
                        });
                    }
                    let owner_row = format!("({bits:0width$b} (ук {small}) (укр {full})");
                    assert!(
                        table.contains(&owner_row),
                        "D{width} missing owner row: {owner_row}"
                    );
                    for name in [small, full] {
                        assert_eq!(
                            crate::semantic_registry::exact_uk_callable_for_source_head(&name),
                            Some(exact),
                            "D{width} source inverse: {name}"
                        );
                    }
                    witnessed += 1;
                }
            }
        }
        assert_eq!(witnessed, 448);
        assert!(
            crate::semantic_registry::exact_uk_callable_for_source_head("caaaaaaaar").is_none(),
            "English spelling cannot be promoted to Ukrainian source"
        );
    }

    #[test]
    fn d8_d9_d10_ukrainian_heads_run_as_real_sens_calls() {
        // The source is executed by the SENS reader/evaluator and its D3
        // CONS law, not by a host-only tree oracle.
        for width in [8usize, 9, 10] {
            for (root, suffix) in [(0b100u16, 0u16), (0b011, 0b101101)] {
                let suffix = suffix & ((1u16 << (width - 3)) - 1);
                let bits = (root << (width - 3)) | suffix;
                let exact = identity(width, bits);
                let mut name = if root == 0b100 {
                    String::from("перше")
                } else {
                    String::from("решта")
                };
                for shift in (0..width - 3).rev() {
                    name.push_str(if (suffix >> shift) & 1 == 1 {
                        "-від-решта"
                    } else {
                        "-від-перше"
                    });
                }
                let operations = (0..width - 3)
                    .map(|shift| (suffix >> shift) & 1 == 1)
                    .chain(std::iter::once(root == 0b011))
                    .collect::<Vec<_>>();
                let mut tree = String::from("(як-є ціль)");
                for rest in operations.iter().rev() {
                    tree = if *rest {
                        format!("(сполучити (як-є інше) {tree})")
                    } else {
                        format!("(сполучити {tree} (як-є інше))")
                    };
                }
                assert_eq!(
                    crate::semantic_registry::exact_uk_callable_for_source_head(&name),
                    Some(exact)
                );
                let program = format!("({name} {tree})");
                let value = crate::eval_program(&program, &mut crate::Session::default())
                    .unwrap_or_else(|error| panic!("D{width}:{bits:b} {program}: {error}"))
                    .value;
                assert_eq!(
                    value,
                    Value::Symbol("ціль".into()),
                    "D{width} selector {name} must execute"
                );
            }
        }
    }

    #[test]
    fn d11_derived_compositions_preserve_car_cdr_partiality() {
        // Усі 512 позитивних D11-композицій уже виконує окремий
        // d11_selector_512_live.rs. Тут незалежна негативна межа:
        // p(CAR(x)) / p(CDR(x)) не мають права приймати атом або ().
        // Немає нового D11 opcode і немає host-підміни SENS-обчислення.
        for bits in [0b1000000000u16, 0b0110101101] {
            let parent = identity(10, bits);
            let name = crate::semantic_registry::selector_ukr_for_exact(parent)
                .expect("ratified D10 parent must have an Ukrainian name");
            for child_head in ["перше", "решта"] {
                for input in ["(як-є опора)", "(як-є ())"] {
                    let program = format!("({name} ({child_head} {input}))");
                    let error = crate::eval_program(&program, &mut crate::Session::default())
                        .expect_err("CAR/CDR-derived selector is undefined on non-pairs");
                    assert_eq!(
                        error.kind,
                        ErrorKind::Type,
                        "D11 child of D10:{bits:010b} must reject {input} as a type error, not reader/transport failure: {error}"
                    );
                }
            }
        }
    }

    // #2016: 0/1 suffix meanings are local to CAR/CDR; they do not become
    // a universal D3-root grammar merely because an exact coordinate exists.
    // D7 stays text/data even when its bits resemble a selector address.
    #[test]
    fn other_d3_roots_do_not_inherit_the_selector_prefix_generator() {
        let mut rejected = 0usize;
        for width in [3usize, 4, 5, 6, 8, 9, 10] {
            for root in [0b000u16, 0b001, 0b010, 0b101, 0b110, 0b111] {
                for suffix in 0..(1u16 << (width - 3)) {
                    let bits = (root << (width - 3)) | suffix;
                    let candidate = identity(width, bits);
                    assert!(
                        decode(candidate).is_none(),
                        "test_id=2016-GENERATOR-LOCAL layer=SENS-mechanism D{width}:{bits:0width$b} expected=not-selector",
                        width = width,
                    );
                    assert!(
                        invoke(candidate, &[Value::Nil], Span::default()).is_none(),
                        "test_id=2016-GENERATOR-LOCAL layer=SENS-mechanism D{width}:{bits:0width$b} expected=no-selector-invocation",
                        width = width,
                    );
                    rejected += 1;
                }
            }
        }
        assert_eq!(rejected, 1434);

        for bits in 0..128u8 {
            let text7 = DomainIdentity::D7(crate::D7DataWord::from_word(
                crate::Bit7::new(bits).unwrap(),
            ));
            assert!(
                decode(text7).is_none(),
                "test_id=2016-TEXT7-BOUNDARY layer=SENS-mechanism D7:{bits:07b} expected=not-selector"
            );
        }
    }

    #[test]
    fn boundary_rejects_d7_nonselector_and_unsupported_arity() {
        // D7:1000000 must never be treated as an extension of D3 CAR.
        assert!(decode(DomainIdentity::D7(crate::D7DataWord::from_word(
            crate::Bit7::new(0b1000000).unwrap()
        )))
        .is_none());
        assert!(decode(identity(8, 0b10100000)).is_none());
        let d10 = identity(10, 0b1000000000);
        assert!(invoke(d10, &[], Span::default()).unwrap().is_err());
        assert!(invoke(d10, &[Value::Nil, Value::Nil], Span::default())
            .unwrap()
            .is_err());
    }
}
