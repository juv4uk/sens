//! #4449 / #3910: RATIFIED D4:1110 LIST is a current value mechanism.
//!
//! These physical T5 programs are independent small Rust runtime witnesses,
//! not claims that historical lib/machine/block.lisp has been migrated.
//! D2 owns structural framing; D4 LIST derives a proper list of evaluated
//! arguments without any new opcode or old SID8 interpretation.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, render_ternary_words_spaced,
    ErrorKind, Session, Value,
};

fn run_physical(words: &str) -> Result<Value, sens::LanguageError> {
    let physical = encode_binary_projection_ternary(words).expect("canonical exact physical T5");
    let opened = open_ternary_program(&physical).expect("real D2 reader accepts physical form");
    assert_eq!(opened, words);
    let decoded = decode_ternary_program(&physical).expect("valid canonical trit stream");
    assert_eq!(render_ternary_words_spaced(&decoded), words);
    assert_eq!(encode_binary_projection_ternary(&opened).unwrap(), physical);
    let parsed = parse_canonical_binary(&opened).expect("current exact-domain D2 form");
    eval_parsed_expressions(&parsed, &mut Session::default()).map(|r| r.value)
}

#[test]
fn ratified_d4_list_zero_arguments_is_exact_structural_empty() {
    let value = run_physical("10 1110 01").expect("D4 LIST() is legal, no values");
    assert_eq!(value, Value::Nil);
}

#[test]
fn ratified_d4_list_of_nested_d3_quote_nil_produces_proper_list_with_nil() {
    // Same nested argument class as the failing original machine-block-one:
    // D3 QUOTE returns structural NIL, then D4 LIST wraps it as one value.
    let value = run_physical("10 1110 00 10 001 00 000 01 01")
        .expect("exact D4 LIST must evaluate D3 QUOTE argument exactly once");
    assert_eq!(value, Value::list([Value::Nil]));
    assert_ne!(value, Value::Nil, "one quoted empty value is not the empty list");
}

#[test]
fn d4_list_keeps_argument_order_and_d1_bit_identity() {
    let value = run_physical(
        "10 1110 00 10 001 00 000 01 00 1 00 0 01",
    ).expect("D4 LIST supports exact heterogeneous value identity");
    assert_eq!(
        value,
        Value::list([Value::Nil, Value::predicate_bit(true), Value::predicate_bit(false)]),
    );
}

#[test]
fn d4_list_never_auto_admits_other_unimplemented_d4_value_mechanisms() {
    let error = run_physical("10 1111 00 10 001 00 000 01 01")
        .expect_err("D4 APPEND is a different ratified law; LIST cannot admit it");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn byte_width_and_d2_boundaries_not_conflated_with_historical_sid8() {
    // D4:1110 (4 bits) != 8-bit legacy 00001110 and != 5-bit 01110.
    let d4 = encode_binary_projection_ternary("10 1110 01").unwrap();
    let old_width = encode_binary_projection_ternary("10 00001110 01").unwrap();
    let widened = encode_binary_projection_ternary("10 01110 01").unwrap();
    assert_ne!(d4, old_width);
    assert_ne!(d4, widened);
    assert!(run_physical("10 1110 00 10 001 00 000 01").is_err(),
            "unclosed D2 LIST must remain invalid rather than execute");
}
