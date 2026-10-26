//! #4455 historical EQ/COND corpus: physical T5M transport observer ONLY.
//! Historical executable names and old expected-branch behavior are NOT
//! active semantics. Current PredicateBit/D3 COND laws have separate tests.

use sens_cli::zig_transport;

const SELECT_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort/eq-cond-select.sens");
const SKIP_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort/eq-cond-skip.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn historical_eq_cond_images_preserve_typed_transport_without_evaluating_old_logic() {
    for physical in [SELECT_T5, SKIP_T5] {
        let words = decode_t5m_via_zig(physical);
        let visible = open_ternary_via_zig(physical);
        let visible_words = sens::parse_binary_source_words(&visible)
            .expect("the visible exact-width projection parses as SENS words")
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        assert_eq!(visible_words, words, "display projection must preserve typed words");
        let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
        assert_eq!(re_encoded, physical);
    }
}

#[test]
fn corrupted_t5m_or_historical_text_is_not_current_binary_source() {
    assert!(zig_transport::decode_t5m_words(&[243]).is_err());
    let mut bad = SELECT_T5.to_vec();
    bad.push(242);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
    let tokens = sens::parse_binary_source_words("(eq (a) (b))");
    assert!(tokens.is_err());
}
