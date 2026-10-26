//! #4467 / #4472: physical Core1 fixture transport and D2 syntax boundary via Zig T5M.
//! Core1 selected-value laws are proved by the SENS/Lisp-owned witness.

use sens_cli::zig_transport;

const T5: &[u8] = include_bytes!("../../../tests/fixtures/core1-domain-canary/second.sens");

#[test]
fn physical_core1_second_canary_preserves_exact_t5m_words() {
    assert_eq!(
        T5.len(),
        22,
        "the committed T5M fixture is exactly 22 bytes"
    );
    // The entrypoint is *physical bytes*, not a handcrafted evaluator value.
    let words = zig_transport::decode_t5m_words(T5).expect("canonical T5M and D2 source structure");
    let visible = sens::render_binary_words_spaced(&words);
    assert_eq!(
        sens_cli::zig_transport::decode_t5m_words(T5)
            .unwrap()
            .into_iter()
            .map(|w| sens::render_binary_words_spaced(&[w]))
            .collect::<Vec<_>>()
            .join(" "),
        visible
    );
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("Zig T5M re-encode");
    assert_eq!(re_encoded, T5);
}

#[test]
fn corrupted_or_legacy_transport_cannot_be_admitted_as_the_core1_canary() {
    let mut trailer = T5.to_vec();
    trailer.push(242); // obsolete EOS "22" block, not canonical file EOF
    assert!(zig_transport::decode_t5m_words(&trailer).is_err());
    assert!(zig_transport::decode_t5m_words(&[243u8]).is_err());
    let tokens = sens::parse_binary_source_words("(CAR (CDR X))");
    assert!(tokens.is_err());
    assert!(sens::parse_canonical_binary("10 100 00 10 011").is_err());
}
