//! #4455: current D1/COND fixture keeps its exact physical T5M representation.
//! Rust is a transport observer here; COND control and result laws belong to Lisp.

use sens_cli::zig_transport;

const T5: &[u8] = include_bytes!("../../../tests/fixtures/migration-d1-cond-cohort/branch.sens");
const SPACED_VIEW: &str = include_str!("../../../tests/fixtures/migration-d1-cond-cohort/branch");
const WORDS: &str = "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01";

#[test]
fn physical_t5m_d1_cond_preserves_source_and_transport_views() {
    assert_eq!(
        T5,
        [0x67, 0x38, 0x65, 0x15, 0xbf, 0x12, 0x3b, 0x2d, 0xc4, 0xa9, 0xb1, 0xa1]
    );
    let words = zig_transport::decode_t5m_words(T5).expect("committed file must be canonical T5M");
    let current = sens::render_binary_words_spaced(&words);
    assert_eq!(current, WORDS);
    assert_eq!(SPACED_VIEW, format!("{current}\n"));
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("Zig T5M re-encode");
    assert_eq!(re_encoded, T5);
    assert_eq!(
        sens_cli::zig_transport::decode_t5m_words(T5)
            .unwrap()
            .into_iter()
            .map(|w| sens::render_binary_words_spaced(&[w]))
            .collect::<Vec<_>>()
            .join(" "),
        WORDS
    );
}

#[test]
fn corrupt_physical_tail_never_falls_back_to_lisp_text() {
    let mut bad = T5.to_vec();
    bad.push(242u8);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
    assert!(zig_transport::decode_t5m_words(&[243u8]).is_err());
    let tokens = sens::parse_binary_source_words("(110 (1 1))");
    assert!(tokens.is_err());
}
