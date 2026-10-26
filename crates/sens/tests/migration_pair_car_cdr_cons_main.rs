//! Bounded physical migration fixtures -> current exact-width T5 round-trip.
use sens::{BinarySourceWord, render_binary_words_spaced, encode_binary_projection_ternary};

use sens_cli::zig_transport;
const CAR_CDR_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens");
const CONS_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort-main/pair-cons.sens");



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
fn car_cdr_migration_roundtrips_exact_t5_words() {
    let expected = "10 100 00 10 011 00 10 001 00 10 000 00 000 01 01 01 01";
    let words = decode_ternary_program(CAR_CDR_T5).expect("canonical physical T5");
    let visible = open_ternary_program(CAR_CDR_T5).expect("T5 opens");
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
fn cons_migration_roundtrips_exact_t5_words() {
    let expected = "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";
    const VIEW: &str = include_str!("../../../tests/fixtures/migration-pair-cohort-main/pair-cons");
    assert_eq!(VIEW, format!("{expected}\n"));
    assert_eq!(VIEW.lines().count(), 1);
    assert!(VIEW
        .bytes()
        .all(|b| matches!(b, b'0' | b'1' | b' ' | b'\n')));
    assert_eq!(
        encode_binary_projection_ternary(VIEW.trim_end()).unwrap(),
        CONS_T5
    );
    let words = decode_ternary_program(CONS_T5).expect("canonical physical T5");
    let visible = open_ternary_program(CONS_T5).expect("T5 opens");
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
fn malformed_t5_is_rejected() {
    for payload in [CAR_CDR_T5, CONS_T5] {
        let mut bad = payload.to_vec();
        bad.push(0xf2);
        assert!(decode_ternary_program(&bad).is_err());
    }
}
