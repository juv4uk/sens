//! #4455 — two top-level D2 forms in one exact physical T5M source.
//! Rust checks transport and syntax boundaries; program-result laws remain Lisp-owned.

use sens_cli::zig_transport;

const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort/two-forms.sens");
const SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-multiform-cohort/two-forms.lisp");
const PROJECTION: &str = "10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn physical_two_form_source_retains_d2_boundary_and_roundtrips() {
    // Provenance linkage only: this test checks the source is the expected
    // two-form input; it does not assert a Rust language result for either form.
    assert_eq!(SOURCE.lines().count(), 2);
    assert_eq!(
        T5,
        [0x63, 0x89, 0x06, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x63, 0x89, 0x06, 0x8c,]
    );
    let words = decode_t5m_via_zig(T5);
    assert_eq!(words.len(), 21);
    let visible = open_ternary_via_zig(T5);
    assert_eq!(
        visible.split_whitespace().nth(5),
        Some("00"),
        "D2 inter-form separator"
    );
    assert_eq!(visible, PROJECTION);
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
    assert_eq!(re_encoded, T5);

    let forms = sens::parse_canonical_binary(&visible).expect("parse two current-domain forms");
    assert_eq!(
        forms.len(),
        2,
        "two top-level forms, not one concatenated datum"
    );
}

#[test]
fn invalid_t5m_tail_never_becomes_a_second_program() {
    assert!(zig_transport::decode_t5m_words(&[243u8]).is_err());
    let mut bad = T5.to_vec();
    bad.push(242u8);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
}
