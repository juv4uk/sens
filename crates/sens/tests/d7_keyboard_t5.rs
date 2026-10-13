//! Current D7 keyboard/v2 exact W7 data through physical T5.
//! In code, quoted function identities come from the domain ladder first.
use sens::{
    decode_d7_uk_t5, decode_ternary_words, encode_d7_uk_t5,
    encode_ternary_words, Bit2, Bit7, BinarySourceWord, D7T5Error,
    TernaryTransportError,
};

#[test]
fn every_w7_keyboard_coordinate_survives_physical_t5() {
    let words: Vec<_> = (0u8..=127)
        .map(|bits| BinarySourceWord::W7(Bit7::new(bits).unwrap()))
        .collect();
    let transport = encode_ternary_words(&words).unwrap();
    assert_eq!(decode_ternary_words(&transport).unwrap(), words);
    let expected: String = (0u8..=127)
        .map(|bits| sens::d7_keyboard::project(bits, sens::d7_keyboard::D7Mode::Uk).unwrap())
        .collect();
    assert_eq!(decode_d7_uk_t5(&transport).unwrap(), expected);
    assert_eq!(encode_d7_uk_t5(&expected).unwrap(), transport);
}

#[test]
fn ukrainian_uppercase_is_one_seven_bit_cell() {
    let physical = encode_d7_uk_t5("Кіт").unwrap();
    let words = decode_ternary_words(&physical).unwrap();
    assert_eq!(words.len(), 3);
    assert!(words.iter().all(|word| word.width() == 7));
    assert_eq!(decode_d7_uk_t5(&physical).unwrap(), "Кіт");
}

#[test]
fn old_reserved_coordinates_are_current_text_data() {
    for (bits, glyph) in [(33, "!"), (42, "*"), (97, "ф")] {
        let physical = encode_ternary_words(&[
            BinarySourceWord::W7(Bit7::new(bits).unwrap()),
        ]).unwrap();
        assert_eq!(decode_d7_uk_t5(&physical).unwrap(), glyph);
    }
}

#[test]
fn d2_grammar_words_do_not_become_d7_text_even_for_same_characters() {
    for bits in [0b00, 0b01, 0b10, 0b11] {
        let bytes = encode_ternary_words(&[
            BinarySourceWord::W2(Bit2::new(bits).unwrap()),
        ]).unwrap();
        assert_eq!(decode_d7_uk_t5(&bytes), Err(D7T5Error::NonD7Word));
    }
    for text in ["(", ")", ".", " ", "\n"] {
        assert_eq!(decode_d7_uk_t5(&encode_d7_uk_t5(text).unwrap()).unwrap(), text);
    }
}

#[test]
fn invalid_unicode_or_bad_physical_byte_fails_closed() {
    assert!(matches!(encode_d7_uk_t5("🙂"), Err(D7T5Error::UnassignedKeyboardGlyph { .. })));
    assert_eq!(decode_d7_uk_t5(&[243]),
               Err(D7T5Error::Transport(TernaryTransportError::InvalidPhysicalByte)));
}
