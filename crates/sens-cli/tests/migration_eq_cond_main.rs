//! Historical EQ/COND migration corpus: typed transport only via Zig T5M.
//! Old 8-bit executable semantics are archaeology, not Rust-owned truth laws.

use sens_cli::zig_transport;

const SELECT_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens");
const SKIP_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn original_eq_cond_images_roundtrip_as_historical_transport_only() {
    for data in [SELECT_T5, SKIP_T5] {
        let words = decode_t5m_via_zig(data);
        let visible = open_ternary_via_zig(data);
        let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
        assert_eq!(re_encoded, data);
    }
}

#[test]
fn corrupt_physical_and_legacy_text_are_rejected() {
    assert!(zig_transport::decode_t5m_words(&[243]).is_err());
    let mut bad = SELECT_T5.to_vec();
    bad.push(242);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
    let tokens = sens::parse_binary_source_words("(eq (a) (b))");
    assert!(tokens.is_err());
}
