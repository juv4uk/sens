//! D4 exact-width carrier and physical T5M transport checks only.
//! LIST/APPEND semantics and resident admission are SENS/Lisp-owned laws.

use sens_cli::zig_transport;

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

fn encode_via_zig(source: &str) -> Vec<u8> {
    let tokens = sens::parse_binary_source_words(source)
        .expect("binary projection parses to exact-width tokens");
    let words = tokens
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    zig_transport::encode_t5m_direct(&words).expect("Zig T5M encoder must produce physical bytes")
}

#[test]
fn width_qualified_words_roundtrip_without_borrowing_cross_domain_meaning() {
    let cases = [
        ("10 1110 01", 4usize, 0b1110u16),
        ("10 1111 01", 4usize, 0b1111u16),
        ("10 01110 01", 5usize, 0b01110u16),
        ("10 00001110 01", 8usize, 0b00001110u16),
    ];

    for (source, expected_width, expected_payload) in cases {
        let physical = encode_via_zig(source);
        let words = decode_t5m_via_zig(&physical);
        assert_eq!(open_ternary_via_zig(&physical), source);
        assert_eq!(encode_via_zig(source), physical);

        let resident = words.get(1).expect("D2 open precedes exact-width head");
        assert_eq!(resident.width(), expected_width);
        assert_eq!(resident.packed_bits(), expected_payload);
    }
}

#[test]
fn physical_t5m_rejects_invalid_bytes_and_noncanonical_trailers() {
    for source in ["10 1110 01", "10 1111 01", "10 01110 01"] {
        let physical = encode_via_zig(source);
        assert!(!decode_t5m_via_zig(&physical).is_empty());

        let mut padded = physical.to_vec();
        padded.push(0xf2);
        assert!(zig_transport::decode_t5m_words(&padded).is_err());
    }
    assert!(zig_transport::decode_t5m_words(&[243u8]).is_err());
}

#[test]
fn exact_width_word_identity_is_preserved_in_the_visible_projection() {
    let d4 = encode_via_zig("10 1110 01");
    let d5 = encode_via_zig("10 01110 01");
    assert_ne!(d4, d5);

    let d4_words = decode_t5m_via_zig(&d4);
    let d5_words = decode_t5m_via_zig(&d5);
    assert_eq!(d4_words[1].packed_bits(), d5_words[1].packed_bits());
    assert_ne!(d4_words[1].width(), d5_words[1].width());
}
