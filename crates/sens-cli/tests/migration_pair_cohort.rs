//! #4455 — bounded historical fixture transport through exact D3/D2 words via Zig T5M.

use sens_cli::zig_transport;

const CAR_CDR_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort/pair-car-cdr.sens");
const CONS_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort/pair-cons.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn car_cdr_fixture_preserves_exact_current_words_and_physical_t5m() {
    let expected = "10 100 00 10 011 00 10 001 00 10 000 00 000 01 01 01 01";
    let words = decode_t5m_via_zig(CAR_CDR_T5);
    let visible = open_ternary_via_zig(CAR_CDR_T5);
    assert_eq!(visible, expected);
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
    assert_eq!(re_encoded, CAR_CDR_T5);
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
fn cons_fixture_preserves_exact_current_words_and_physical_t5m() {
    let expected = "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";
    let words = decode_t5m_via_zig(CONS_T5);
    let visible = open_ternary_via_zig(CONS_T5);
    assert_eq!(visible, expected);
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
    assert_eq!(re_encoded, CONS_T5);
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
fn malformed_physical_t5m_fails_closed_for_both_migrated_programs() {
    for payload in [CAR_CDR_T5, CONS_T5] {
        let mut corrupt = payload.to_vec();
        corrupt.push(0xf2);
        assert!(zig_transport::decode_t5m_words(&corrupt).is_err());
    }
}
