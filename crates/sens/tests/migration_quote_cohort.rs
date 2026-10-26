//! #4455 — фізичний T5M round-trip for historical quote cohort; laws remain Lisp-owned.

use sens_cli::zig_transport;

const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort/quote-legacy.sens");
const MYLISP_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort/quote-mylisp.sens");
const LISP15_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort/quote-lisp15.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn physical_quote_legacy_migration_preserves_exact_t5m_transport() {
    assert_eq!(T5, [0x63, 0x89, 0x06, 0xa1]);
    let words = decode_t5m_via_zig(T5);
    let visible = open_ternary_via_zig(T5);
    assert_eq!(visible, "10 001 00 000 01");
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
    assert_eq!(re_encoded, T5);
}

#[test]
fn alternate_physical_quote_artifacts_preserve_identical_t5m_bytes() {
    for payload in [MYLISP_T5, LISP15_T5] {
        assert_eq!(payload, T5);
        let visible = open_ternary_via_zig(payload);
        assert_eq!(visible, "10 001 00 000 01");
    }
}

#[test]
fn invalid_t5m_bytes_cannot_be_substituted_for_a_migrated_program() {
    assert!(zig_transport::decode_t5m_words(&[243u8]).is_err());
    let mut bad = T5.to_vec();
    bad.push(242u8);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
    let tokens = sens::parse_binary_source_words("(00000001 ())");
    assert!(tokens.is_err());
}
