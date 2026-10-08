//! Current reference execution for ALREADY-RATIFIED D4 compact-derived LIST/APPEND.
//! D4 identity is not a historical W8/SID alias; all values remain D3 Pair/Nil.
//! This bridges executable semantics, NOT owner approval of Text7 wire framing.
use sens::{
    encode_binary_projection_ternary, eval_parsed_expressions, open_ternary_program,
    parse_canonical_binary, ErrorKind, Session, Value,
};

fn run(words: &str) -> Result<Value, sens::LanguageError> {
    let physical = encode_binary_projection_ternary(words).expect("exact binary T5 physical");
    assert_eq!(
        open_ternary_program(&physical).expect("real canonical Rust D2 reader"),
        words
    );
    let expressions = parse_canonical_binary(words).expect("well-formed D2");
    eval_parsed_expressions(&expressions, &mut Session::default()).map(|r| r.value)
}

#[test]
fn d4_list_zero_one_and_two_values_yield_proper_lists() {
    assert!(matches!(run("10 1110 01").unwrap(), Value::Nil));
    let singleton = run("10 1110 00 000 01").unwrap();
    assert_eq!(singleton.to_string(), "(())");
    // D1:0 and D3:000 remain different carriers when inserted into LIST.
    let pair = run("10 1110 00 0 00 000 01").unwrap();
    assert_eq!(pair.to_string(), "(0 ())");
}

#[test]
fn d4_append_zero_and_two_proper_lists_preserves_order() {
    assert!(matches!(run("10 1111 01").unwrap(), Value::Nil));
    let two = "10 1111 00 10 1110 00 000 01 00 10 1110 00 000 01 01";
    assert_eq!(run(two).unwrap().to_string(), "(() ())");
    let skip_empty = "10 1111 00 000 00 10 1110 00 000 01 01";
    assert_eq!(run(skip_empty).unwrap().to_string(), "(())");
}

#[test]
fn d4_append_only_admits_proper_lists_not_predicates_or_improper_pairs() {
    let bad_predicate = run("10 1111 00 1 01").unwrap_err();
    assert_eq!(bad_predicate.kind, ErrorKind::Type);
    assert!(bad_predicate.message.contains("proper lists"));

    // APPEND of an explicit dotted pair is prohibited: no silent tail coercion.
    let dotted =
        "10 1111 00 10 001 00 10 1 11 0 01 01";
    let bad_dotted = run(dotted).unwrap_err();
    assert_eq!(bad_dotted.kind, ErrorKind::Type);
    assert!(bad_dotted.message.contains("proper lists"));
}

#[test]
fn only_two_ratified_d4_derived_coordinates_acquire_a_mechanism() {
    // D4:1101 EVLIS must never be promoted by an arithmetic/bitmask trick.
    let unsupported = run("10 1101 00 000 01").unwrap_err();
    assert_eq!(unsupported.kind, ErrorKind::Type);
    assert!(unsupported.message.contains("no admitted value-call mechanism"));
}

#[test]
fn equal_numeric_payloads_in_other_widths_never_borrow_d4_list_meaning() {
    // D4:1110 LIST is the exact four-bit resident. Same numeric payloads in
    // other widths are different identities and must not inherit LIST.
    let d5_same_bits = run("10 01110 01").unwrap_err();
    assert_ne!(d5_same_bits.message, "");
    assert!(
        d5_same_bits.message.contains("no admitted value-call mechanism")
            || d5_same_bits.kind == ErrorKind::Type
    );

    let d8_same_bits = run("10 00001110 01").unwrap_err();
    assert_ne!(d8_same_bits.message, "");
    assert!(
        d8_same_bits.message.contains("no admitted value-call mechanism")
            || d8_same_bits.kind == ErrorKind::Type
    );
}

#[test]
fn d4_list_and_append_proof_does_not_change_quote_data_or_d3_empty() {
    assert!(matches!(run("000").unwrap(), Value::Nil));
    let quoted = run("10 001 00 10 1110 00 000 01 01").unwrap();
    // A quoted list containing D4 LIST code stays data; never a call.
    assert!(!matches!(quoted, Value::Nil));
}
