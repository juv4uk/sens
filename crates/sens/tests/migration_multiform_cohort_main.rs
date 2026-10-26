//! Bounded real migration: two historical top-level forms -> one exact physical T5M stream.

use sens_cli::zig_transport;

const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");
const PROJECTION: &str = "10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn two_forms_roundtrip_and_retain_d2_form_boundaries() {
    assert_eq!(
        T5,
        [0x63, 0x89, 0x06, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x63, 0x89, 0x06, 0x8c]
    );
    let words = decode_t5m_via_zig(T5);
    assert_eq!(words.len(), 21);
    let visible = open_ternary_via_zig(T5);
    assert_eq!(visible, PROJECTION);
    assert_eq!(visible.split_whitespace().nth(5), Some("00"));
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
    assert_eq!(re_encoded, T5);
    let forms = sens::parse_canonical_binary(&visible).expect("two current-domain forms");
    assert_eq!(forms.len(), 2);
}

#[test]
fn corrupt_t5m_is_rejected() {
    let mut bad = T5.to_vec();
    bad.push(0xf2);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
}
