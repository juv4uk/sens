//! Current D7 keyboard/v2 exact W7 data through physical T5M.
//! In code, quoted function identities come from the domain ladder first.

use sens::{decode_d7_uk_t5, encode_d7_uk_t5, BinarySourceWord, Bit2, Bit7, D7T5Error};
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

#[test]
fn every_w7_keyboard_coordinate_survives_physical_t5m() {
    let words: Vec<_> = (0u8..=127)
        .map(|bits| BinarySourceWord::W7(Bit7::new(bits).unwrap()))
        .collect();
    let transport = encode_via_zig(&sens::render_binary_words_spaced(&words));
    let recovered = decode_t5m_via_zig(&transport);
    assert_eq!(recovered, words);
    let expected: String = (0u8..=127)
        .map(|bits| sens::d7_keyboard::project(bits, sens::d7_keyboard::D7Mode::Uk).unwrap())
        .collect();
    assert_eq!(decode_d7_uk_t5(&transport).unwrap(), expected);
    assert_eq!(encode_d7_uk_t5(&expected).unwrap(), transport);
}

#[test]
fn ukrainian_uppercase_is_one_seven_bit_cell() {
    let physical = encode_d7_uk_t5("Кіт").unwrap();
    let words = decode_t5m_via_zig(&physical);
    assert_eq!(words.len(), 3);
    assert!(words.iter().all(|word| word.width() == 7));
    assert_eq!(decode_d7_uk_t5(&physical).unwrap(), "Кіт");
}

#[test]
fn old_reserved_coordinates_are_current_text_data() {
    for (bits, glyph) in [(33, "!"), (42, "*"), (97, "ф")] {
        let physical = encode_d7_uk_t5(glyph).unwrap();
        let words = decode_t5m_via_zig(&physical);
        assert_eq!(words.len(), 1);
        assert_eq!(words[0].width(), 7);
        assert_eq!(decode_d7_uk_t5(&physical).unwrap(), glyph);
    }
}

#[test]
fn d2_grammar_words_do_not_become_d7_text_even_for_same_characters() {
    for bits in [0b00, 0b01, 0b10, 0b11] {
        let words = vec![BinarySourceWord::W2(Bit2::new(bits).unwrap())];
        let physical = zig_transport::encode_t5m_direct(&words).unwrap();
        assert_eq!(decode_d7_uk_t5(&physical), Err(D7T5Error::NonD7Word));
    }
    for text in ["(", ")", ".", " ", "\n"] {
        let physical = encode_d7_uk_t5(text).unwrap();
        let words = decode_t5m_via_zig(&physical);
        assert_eq!(decode_d7_uk_t5(&physical).unwrap(), text);
    }
}

#[test]
fn d7_stack_glyph_projection_preserves_t5m_and_multibyte_error_offset() {
    let source = "Кіт! (.)\n";
    let physical = encode_d7_uk_t5(source).expect("admitted Ukrainian D7");
    let words = decode_t5m_via_zig(&physical);
    assert_eq!(
        words.len(),
        source.chars().count(),
        "one D7 word per Unicode scalar"
    );
    assert!(words.iter().all(|word| word.width() == 7), "no D2/D8 alias");
    assert_eq!(
        decode_d7_uk_t5(&physical),
        Ok(source.to_string()),
        "same exact W7 identities after physical roundtrip"
    );
    assert_eq!(
        encode_via_zig(&sens::render_binary_words_spaced(&words)),
        physical,
        "stack projection must not modify packed T5M bytes"
    );

    // 'К' and 'і' occupy two UTF-8 bytes each. The third scalar is not D7;
    // offset reports the first byte, not a character ordinal or host number.
    assert_eq!(
        encode_d7_uk_t5("Кі🙂"),
        Err(D7T5Error::UnassignedKeyboardGlyph { byte_offset: 4 })
    );
}

#[test]
fn d7_repeated_utf8_uses_exact_words_without_post_encode_decode() {
    let segment = "Кіт! (.)\n";
    let source = segment.repeat(31);
    let segment_physical = encode_d7_uk_t5(segment).unwrap();
    let segment_words = decode_t5m_via_zig(&segment_physical);
    let expected_words: Vec<_> = (0..31)
        .flat_map(|_| segment_words.iter().copied())
        .collect();
    let packed = encode_d7_uk_t5(&source).unwrap();
    assert_eq!(
        packed,
        encode_via_zig(&sens::render_binary_words_spaced(&expected_words)),
        "T5M bytes must match the independent W7 encoding"
    );
    let actual = decode_t5m_via_zig(&packed);
    assert_eq!(actual, expected_words, "all W7 bits and boundaries survive");
    assert!(
        actual.iter().all(|word| word.width() == 7),
        "no implicit D2/D8"
    );
    assert_eq!(decode_d7_uk_t5(&packed).unwrap(), source);
    assert_eq!(
        encode_d7_uk_t5(&(source.clone() + "🙂")),
        Err(D7T5Error::UnassignedKeyboardGlyph {
            byte_offset: source.len()
        })
    );
}

#[test]
fn invalid_unicode_or_bad_physical_byte_fails_closed() {
    assert!(matches!(
        encode_d7_uk_t5("🙂"),
        Err(D7T5Error::UnassignedKeyboardGlyph { .. })
    ));
    assert!(zig_transport::decode_t5m_words(&[243]).is_err());
}
