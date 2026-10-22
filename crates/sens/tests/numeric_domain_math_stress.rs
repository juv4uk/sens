//! Independent, reproducible signed D24+ arithmetic acceptance suite.
//! Host i128 is an independent oracle only; SENS identity remains exact bits
//! plus the explicitly admitted Dn width.
use sens::{domain_numeric_value, eval_program, BinaryNumber, Session, Value};

fn signed_word(width: usize, value: i128) -> BinaryNumber {
    assert!(width < 128);
    let modulus = 1u128 << width;
    let encoded = (value as u128) & (modulus - 1);
    let bits = (0..width)
        .map(|index| ((encoded >> (width - 1 - index)) & 1) as u8)
        .collect::<Vec<_>>();
    BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap()
}

fn signed_oracle(width: usize, raw: u64) -> i128 {
    let modulus = 1u128 << width;
    let encoded = u128::from(raw) & (modulus - 1);
    if encoded & (1u128 << (width - 1)) != 0 {
        encoded as i128 - modulus as i128
    } else {
        encoded as i128
    }
}

fn integer(value: Value) -> (usize, i128) {
    let Value::BinaryNumber(ref number) = value else {
        panic!("integer arithmetic must return a Dn word")
    };
    (
        number.numeric_domain_width().expect("explicit Dn identity"),
        number
            .to_decimal_string()
            .parse()
            .expect("exact signed decimal oracle view"),
    )
}

fn fits_signed(value: i128, width: usize) -> bool {
    let bound = 1i128 << (width - 1);
    -bound <= value && value < bound
}

fn next(seed: &mut u64) -> u64 {
    // Fixed deterministic pseudorandom witness stream; no external crates.
    *seed ^= *seed << 13;
    *seed ^= *seed >> 7;
    *seed ^= *seed << 17;
    *seed
}

#[test]
fn independent_oracle_18000_cases_of_signed_d24_d48_arithmetic() {
    let mut seed = 0xA53C_1967_1B97_F00Du64;
    for (width, trials) in [(24usize, 12000usize), (48, 6000)] {
        for _ in 0..trials {
            let a = signed_oracle(width, next(&mut seed));
            let b = signed_oracle(width, next(&mut seed));
            let left = Value::BinaryNumber(signed_word(width, a));
            let right = Value::BinaryNumber(signed_word(width, b));

            for (operator, expected) in [("+", a + b), ("-", a - b), ("*", a * b)] {
                let result = domain_numeric_value(operator, &left, &right)
                    .unwrap_or_else(|| panic!("D{width} {a} {operator} {b} rejected"));
                let (actual_width, actual) = integer(result);
                assert_eq!(actual, expected, "D{width}: {a} {operator} {b}");
                assert_eq!(
                    actual_width,
                    if fits_signed(expected, width) {
                        width
                    } else {
                        2 * width
                    }
                );
            }
        }
    }
}

#[test]
fn signed_d24_plus_boundaries_extend_without_wrap_or_lost_bits() {
    for width in [24usize, 48, 96, 192, 384] {
        let zero = vec![0; width];
        let mut one = vec![0; width];
        one[width - 1] = 1;
        let minus_one = vec![1; width];
        let mut maximum = vec![1; width];
        maximum[0] = 0;
        let mut minimum = vec![0; width];
        minimum[0] = 1;

        let admit = |bits: &[u8]| {
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, bits).unwrap())
        };
        let max_plus_one = domain_numeric_value("+", &admit(&maximum), &admit(&one)).unwrap();
        let Value::BinaryNumber(ref carried) = max_plus_one else {
            panic!("integer result")
        };
        assert_eq!(carried.numeric_domain_width(), Some(2 * width));
        let mut positive_carry = vec![0; 2 * width];
        positive_carry[width] = 1; // +2^(width-1), exact two's-complement D(2n)
        assert_eq!(
            carried.exact_numeric_domain_bits(),
            Some(positive_carry.clone())
        );

        let min_minus_one = domain_numeric_value("-", &admit(&minimum), &admit(&one)).unwrap();
        let Value::BinaryNumber(ref widened_negative) = min_minus_one else {
            panic!("integer result")
        };
        assert_eq!(widened_negative.numeric_domain_width(), Some(2 * width));
        let mut negative_below_minimum = vec![1; 2 * width];
        negative_below_minimum[width] = 0; // -(2^(width-1)+1)
        assert_eq!(
            widened_negative.exact_numeric_domain_bits(),
            Some(negative_below_minimum)
        );

        let negated_minimum =
            domain_numeric_value("*", &admit(&minimum), &admit(&minus_one)).unwrap();
        let Value::BinaryNumber(ref positive_minimum) = negated_minimum else {
            panic!("integer result")
        };
        assert_eq!(
            positive_minimum.exact_numeric_domain_bits(),
            Some(positive_carry)
        );

        let all_ones_plus_one =
            domain_numeric_value("+", &admit(&minus_one), &admit(&one)).unwrap();
        assert_eq!(all_ones_plus_one, admit(&zero));
    }
}

#[test]
fn domain_inference_and_mixed_width_coercion_remain_forbidden() {
    let d24 = Value::BinaryNumber(signed_word(24, 17));
    let d48 = Value::BinaryNumber(signed_word(48, 17));
    assert_ne!(d24, d48);
    for (left, right) in [
        (d24.clone(), d48.clone()),
        (d48.clone(), d24.clone()),
        (
            d24.clone(),
            Value::BinaryNumber(BinaryNumber::from_bits([1, 0, 0, 0, 1]).unwrap()),
        ),
    ] {
        for operator in ["+", "-", "*", "/"] {
            assert!(domain_numeric_value(operator, &left, &right).is_none());
        }
    }
}

#[test]
fn real_core_session_runs_signed_math_and_ratio_composition() {
    let mut session = Session::default();
    session
        .environment
        .define("a", Value::BinaryNumber(signed_word(24, -2)));
    session
        .environment
        .define("b", Value::BinaryNumber(signed_word(24, 3)));

    for (expression, expected) in [("(+ a b)", "1"), ("(* a b)", "-6"), ("(- a b)", "-5")] {
        let result = eval_program(expression, &mut session)
            .expect("Core signed D24 math")
            .value;
        assert_eq!(result.to_string(), expected, "{expression}");
    }

    let ratio = domain_numeric_value(
        "/",
        &Value::BinaryNumber(signed_word(24, -2)),
        &Value::BinaryNumber(signed_word(24, 3)),
    )
    .expect("exact signed ratio");
    assert_eq!(ratio.to_string(), "-2/3");
    assert!(domain_numeric_value(
        "/",
        &Value::BinaryNumber(signed_word(24, 1)),
        &Value::BinaryNumber(signed_word(24, 0))
    )
    .is_none());
}
