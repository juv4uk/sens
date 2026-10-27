//! Physical T5M D2/D7 contextual binding witness; no ASCII Lisp fallback.
//! D2 owns structure, D7 owns exact Text7 cells, D4 owns LAMBDA.
//! This proves physical T5M can carry D7 contextual identifiers without
//! treating arbitrary untyped D2/W7 data as executable symbols.

use sens_cli::zig_transport;

#[test]
fn canonical_t5m_d2_d7_has_no_raw_textual_source_backdoor() {
    // D2/W7 data is valid physical data but isn't automatically a function.
    let data = "10 1101010 01";

    fn encode_via_zig(source: &str) -> Vec<u8> {
        let tokens = sens::parse_binary_source_words(source)
            .expect("binary projection parses to exact-width tokens");
        let words = tokens
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        zig_transport::encode_t5m_direct(&words)
            .expect("Zig T5M encoder must produce physical bytes")
    }

    let physical = encode_via_zig(data);
    assert_eq!(zig_transport::decode_t5m_words(&physical).unwrap().len(), 3);
    assert_eq!(open_ternary_via_zig(&physical), data);
    // The old host Lisp oracle must not be declared canonical by its
    // presence in a D2 structure: nonbinary identifiers stay rejected.
    let tokens = sens::parse_binary_source_words("(00001001 identity (00001000 (value) value))");
    assert!(tokens.is_err());
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder");
    sens::render_binary_words_spaced(&words)
}
