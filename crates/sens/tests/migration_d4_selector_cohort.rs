//! #4455: migrated historical Lisp I CAAR (D4:1000), nested D3 CONS/QUOTE,
//! physical T5 + current exact-width Rust oracle. No new selector mechanism.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, Session, Value,
};

const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-d4-selector-cohort/caar.sens");
const VISIBLE: &str = "10 1000 00 10 111 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 00 10 001 00 000 01 01 01";
const UKR_SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-d4-selector-cohort/caar.lisp");
const SPACED_VIEW: &str =
    include_str!("../../../tests/fixtures/migration-d4-selector-cohort/caar");
const EXPECTED_PHYSICAL: &[u8] = &[0x66, 0x12, 0xc4, 0x7e, 0xc4, 0x7e, 0xc3, 0x2d, 0xa4, 0x2d, 0xc3, 0x2d, 0xa4, 0x2e, 0xa9, 0x37, 0xa8, 0x13, 0xb1, 0xa1];

#[test]
fn historical_caar_is_a_real_exact_d4_selector_and_returns_nil() {
    assert_eq!(T5, EXPECTED_PHYSICAL);
    let words = decode_ternary_program(T5).expect("must decode canonical physical T5");
    let visible = open_ternary_program(T5).expect("retain exact D1..D9 word widths");
    assert_eq!(visible, VISIBLE);
    assert_eq!(SPACED_VIEW, format!("{VISIBLE}\n"));
    assert!(UKR_SOURCE.starts_with("(п-п (сполучити"));
    assert!(!UKR_SOURCE.contains("CAAR"));
    assert_eq!(SPACED_VIEW.matches('\n').count(), 1);
    assert!(SPACED_VIEW
        .bytes()
        .all(|b| matches!(b, b'0' | b'1' | b' ' | b'\n')));
    assert_eq!(encode_binary_projection_ternary(SPACED_VIEW.trim_end()).unwrap(), T5);
    assert_eq!(
        words.iter().map(ToString::to_string).collect::<Vec<_>>().join(" "),
        VISIBLE
    );
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);
    let ast = parse_canonical_binary(&visible).expect("ratified D2 syntax");
    let result = eval_parsed_expressions(&ast, &mut Session::default())
        .expect("current D4:1000 CAAR composes D3 CAR twice");
    assert!(matches!(result.value, Value::Nil));
}

#[test]
fn d4_selector_must_reject_wrong_arity_not_infer_d3_car() {
    let ast = parse_canonical_binary("10 1000 01").expect("well-formed exact D2");
    assert!(
        eval_parsed_expressions(&ast, &mut Session::default()).is_err(),
        "D4:1000 expects exactly one argument"
    );
    assert!(
        encode_binary_projection_ternary("10 CAAR 00 000 01").is_err(),
        "English surface cannot masquerade as physical SENS"
    );
}

#[test]
fn corrupted_t5_tail_cannot_be_accepted_as_semantics() {
    let mut tampered = T5.to_vec();
    tampered.push(0xf2);
    assert!(decode_ternary_program(&tampered).is_err());
    assert!(decode_ternary_program(&[243u8]).is_err());
}
