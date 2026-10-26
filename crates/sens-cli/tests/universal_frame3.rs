//! Перевірка фізичного Zig/T5M на публічній межі sens-cli.
//! Приватні E1-інваріанти перевіряються всередині sens::universal_frame3.

use ::sens::parse_binary_source_words;

#[test]
fn canonical_word_sequences_roundtrip_through_physical_zig_t5m() {
    for source in [
        "10 001 01",
        "10 000000001 01",
        "10 111111111 01",
        "10 0 00 1 01",
        "10 1 11 0 01",
    ] {
        let words = parse_binary_source_words(source)
            .expect("canonical source words")
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        let physical = sens_cli::zig_transport::encode_t5m_direct(&words)
            .expect("Zig/T5M accepts complete canonical words");
        let recovered = sens_cli::zig_transport::decode_t5m_words(&physical)
            .expect("Zig/T5M decodes its physical carrier");
        assert_eq!(recovered, words, "word identity changed for source={source}");
        for end in 0..physical.len() {
            assert!(
                sens_cli::zig_transport::decode_t5m_words(&physical[..end]).is_err(),
                "truncated physical carrier was accepted: source={source} end={end}"
            );
        }
    }
}
