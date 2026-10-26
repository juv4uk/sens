//! Physical T5M round-trip canary for exact-width binary source.
//! QUOTE's result law is owned by the SENS/Lisp witness, not Rust.

use sens_cli::zig_transport;

const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");

#[test]
fn migrated_quote_fixture_preserves_exact_physical_t5m() {
    assert_eq!(T5, [0x63, 0x89, 0x06, 0xa1]);

    let words = zig_transport::decode_t5m_words(T5).expect("canonical T5M bytes");
    let visible = sens::render_binary_words_spaced(&words);
    assert_eq!(visible, "10 001 00 000 01");
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("Zig T5M re-encode");
    assert_eq!(re_encoded, T5);
    assert_eq!(
        words
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(" "),
        visible
    );
}
