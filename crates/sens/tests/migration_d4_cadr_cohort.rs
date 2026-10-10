//! D4 CADR migration: exact-width source and physical T5 are mechanical.
//! Semantic CADR law belongs to ratified D4 and is checked separately by
//! running SENS against the committed specimen, not by a Rust-owned alias.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, open_ternary_program,
    parse_canonical_word_sequence,
};

const T5: &[u8] = include_bytes!("../../../tests/fixtures/migration-d4-cadr-cohort/cadr.sens");
const VIEW: &str = include_str!("../../../tests/fixtures/migration-d4-cadr-cohort/cadr");

#[test]
fn cadr_ukrainian_t5_preserves_d4_and_d3_exact_widths() {
    assert_eq!(T5.len(), 20, "real packed bytes, not ASCII pseudo-binary");
    let words = decode_ternary_program(T5).expect("canonical physical T5");
    assert_eq!(words.len(), 29);
    assert_eq!(words[0].to_string(), "10");
    assert_eq!(words[1].to_string(), "1001"); // D4 CADR, not D3 CAR
    let visible = open_ternary_program(T5).expect("physical opens as exact words");
    assert_eq!(format!("{visible}\n"), VIEW);
    assert_eq!(encode_binary_projection_ternary(VIEW).unwrap(), T5);
    let expressions = parse_canonical_word_sequence(&words).expect("structural D2 reader");
    assert_eq!(expressions.len(), 1);
}

#[test]
fn cadr_t5_invalid_tail_and_byte_fail_closed() {
    let mut invalid = T5.to_vec();
    invalid.push(242);
    assert!(decode_ternary_program(&invalid).is_err());
    assert!(decode_ternary_program(&[243]).is_err());
}
