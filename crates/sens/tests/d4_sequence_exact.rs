//! Current Rust D4 LIST/APPEND mechanisms on ACTUAL physical T5 memory bytes.
//! Ratified identity source: lib/domains/d4.lisp, structural APPEND derivation #2347.
//! This test does NOT publish nor admit lib/machine/block.sens.

use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, Session,
};

fn execute_physical_exact(words: &str) -> String {
    let bytes = encode_binary_projection_ternary(words).expect("pack real T5");
    let decoded = decode_ternary_program(&bytes).expect("decode physical T5");
    let opened = open_ternary_program(&bytes).expect("exact width open");
    assert_eq!(opened, words);
    assert_eq!(decoded.iter().map(ToString::to_string).collect::<Vec<_>>().join(" "), words);
    assert_eq!(encode_binary_projection_ternary(&opened).unwrap(), bytes);
    let ast = parse_canonical_binary(&opened).expect("canonical D2 parse");
    eval_parsed_expressions(&ast, &mut Session::default())
        .expect("Rust current exact resident execution")
        .value
        .to_string()
}

#[test]
fn d4_exact_list_executes_after_physical_decode_not_eight_bit_compatibility() {
    // Exact 1110 must remain FOUR bits, not historical 8-bit LIST.
    let empty = "10 1110 01";
    assert_eq!(execute_physical_exact(empty), "()");
    let singleton_nil = "10 1110 00 10 001 00 000 01 01";
    assert_eq!(execute_physical_exact(singleton_nil), "(())");
    let two_nil = "10 1110 00 10 001 00 000 01 00 10 001 00 000 01 01";
    assert_eq!(execute_physical_exact(two_nil), "(() ())");
}

#[test]
fn d4_append_appends_lists_without_losing_nil_payload() {
    let exact = "10 1111 00 10 1110 00 10 001 00 000 01 01 00 10 1110 00 10 001 00 000 01 01 01";
    assert_eq!(execute_physical_exact(exact), "(() ())");

    // APPEND of empty left is identity on right, not a new D3 or D5 law.
    let left_empty = "10 1111 00 10 001 00 000 01 00 10 1110 00 10 001 00 000 01 01 01";
    assert_eq!(execute_physical_exact(left_empty), "(())");
}

#[test]
fn d4_append_refuses_wrong_arity_and_unproved_improper_left() {
    let no_arg = "10 1111 01";
    let one_arg = "10 1111 00 10 001 00 000 01 01";
    for words in [no_arg, one_arg] {
        let bytes = encode_binary_projection_ternary(words).unwrap();
        let visible = open_ternary_program(&bytes).unwrap();
        let ast = parse_canonical_binary(&visible).unwrap();
        assert!(eval_parsed_expressions(&ast, &mut Session::default()).is_err());
    }
    // D2 dotted data is not a proper left list.
    let improper = "10 1111 00 10 001 00 10 1 11 0 01 01 00 10 001 00 000 01 01";
    let bytes = encode_binary_projection_ternary(improper).expect("well-formed T5 terms");
    let visible = open_ternary_program(&bytes).unwrap();
    let ast = parse_canonical_binary(&visible).expect("dotted source is legal D2 data");
    assert!(eval_parsed_expressions(&ast, &mut Session::default()).is_err());
}
