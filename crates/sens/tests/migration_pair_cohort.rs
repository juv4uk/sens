//! #4455 — bounded historical fixture transport through exact D3/D2 words.
use sens::{BinarySourceWord, render_binary_words_spaced, encode_binary_projection_ternary};

use sens_cli::zig_transport;
const CAR_CDR_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort/pair-car-cdr.sens");
const CONS_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort/pair-cons.sens");



// Обгортки над чинним Zig T5M: staged-out ternary виведено (f5a5b213).
fn decode_ternary_program(bytes: &[u8]) -> Result<Vec<BinarySourceWord>, String> {
    zig_transport::decode_t5m_words(bytes)
}

fn open_ternary_program(bytes: &[u8]) -> Result<String, String> {
    zig_transport::decode_t5m_words(bytes).map(|words| render_binary_words_spaced(&words))
}

fn encode_binary_projection_ternary(source: &str) -> Result<Vec<u8>, String> {
    let words: Vec<BinarySourceWord> = sens::parse_binary_source_words(source)
        .map_err(|error| format!("{error:?}"))?
        .into_iter()
        .map(|token| token.word)
        .collect();
    zig_transport::encode_t5m_direct(&words)
}

#[test]
fn car_cdr_fixture_preserves_exact_current_words_and_physical_t5() {
    let expected = "10 100 00 10 011 00 10 001 00 10 000 00 000 01 01 01 01";
    let words = decode_ternary_program(CAR_CDR_T5).expect("canonical physical T5");
    let visible = open_ternary_program(CAR_CDR_T5).expect("canonical T5 opens");
    assert_eq!(visible, expected);
    assert_eq!(
        encode_binary_projection_ternary(&visible).unwrap(),
        CAR_CDR_T5
    );
    assert_eq!(
        words
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(" "),
        expected
    );
}

#[test]
fn cons_fixture_preserves_exact_current_words_and_physical_t5() {
    let expected = "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";
    let words = decode_ternary_program(CONS_T5).expect("canonical physical T5");
    let visible = open_ternary_program(CONS_T5).expect("canonical T5 opens");
    assert_eq!(visible, expected);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), CONS_T5);
    assert_eq!(
        words
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(" "),
        expected
    );
}

#[test]
fn malformed_physical_t5_fails_closed_for_both_migrated_programs() {
    for payload in [CAR_CDR_T5, CONS_T5] {
        let mut corrupt = payload.to_vec();
        corrupt.push(0xf2);
        assert!(decode_ternary_program(&corrupt).is_err());
    }
}
