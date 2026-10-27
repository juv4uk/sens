//! Винятково фізичний Zig T5M: точні W7 слова і межі, без D7-проєкцій мовного змісту.
use sens::{BinarySourceWord, Bit7};
use sens_cli::zig_transport;

fn encode_via_zig(source: &str) -> Vec<u8> {
    let tokens = sens::parse_binary_source_words(source)
        .expect("binary projection parses to exact-width tokens");
    let words = tokens.into_iter().map(|token| token.word).collect::<Vec<_>>();
    zig_transport::encode_t5m_direct(&words)
        .expect("Zig T5M encoder must produce physical bytes")
}

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

#[test]
fn every_w7_keyboard_coordinate_survives_physical_t5m() {
    let words: Vec<_> = (0u8..=127)
        .map(|bits| BinarySourceWord::W7(Bit7::new(bits).unwrap()))
        .collect();
    let transport = encode_via_zig(&sens::render_binary_words_spaced(&words));
    let recovered = decode_t5m_via_zig(&transport);
    assert_eq!(recovered, words);
}
