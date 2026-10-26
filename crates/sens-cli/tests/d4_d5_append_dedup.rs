//! Exact-width D4/D5 carrier tests only via Zig T5M.
//! APPEND/CAAR laws belong to SENS/Lisp.

use sens_cli::zig_transport;

fn encode_via_zig(source: &str) -> Vec<u8> {
    let tokens = sens::parse_binary_source_words(source)
        .expect("binary projection parses to exact-width tokens");
    let words = tokens
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    zig_transport::encode_t5m_direct(&words).expect("Zig T5M encoder must produce physical bytes")
}

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn same_transport_grammar_keeps_d4_and_d5_residents_width_qualified() {
    let cases = [
        ("10 1111 01", 4usize, 0b1111u16),
        ("10 10000 01", 5usize, 0b10000u16),
    ];
    for (source, width, payload) in cases {
        let physical = encode_via_zig(source);
        let words = decode_t5m_via_zig(&physical);
        assert_eq!(open_ternary_via_zig(&physical), source);
        assert_eq!(encode_via_zig(source), physical);
        assert_eq!(words[1].width(), width);
        assert_eq!(words[1].packed_bits(), payload);
    }
}

#[test]
fn same_payload_in_d4_and_d5_cannot_collapse_to_one_coordinate() {
    let d4 = encode_via_zig("10 1111 01");
    let d5 = encode_via_zig("10 01111 01");
    assert_ne!(d4, d5);
    let d4_words = decode_t5m_via_zig(&d4);
    let d5_words = decode_t5m_via_zig(&d5);
    assert_eq!(d4_words[1].packed_bits(), d5_words[1].packed_bits());
    assert_ne!(d4_words[1].width(), d5_words[1].width());
}

#[test]
fn malformed_t5m_never_becomes_a_d4_or_d5_operation() {
    assert!(zig_transport::decode_t5m_words(&[243u8]).is_err());
    let mut bad = encode_via_zig("10 1111 01");
    bad.push(0xf2);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
}
