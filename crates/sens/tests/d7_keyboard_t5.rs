//! D7 Ukrainian keyboard <-> exact W7 <-> physical T5 integration.
//! Sanskrit IAST/Devanagari/SLP1 are script projections, not English glyphs.
use sens::{
    decode_d7_uk_t5, decode_ternary_words, encode_d7_uk_t5,
    encode_ternary_words, Bit2, Bit7, BinarySourceWord, D7T5Error,
    TernaryTransportError,
};

#[test]
fn ukrainian_three_symbols_have_five_exact_t5_bytes() {
    let physical = encode_d7_uk_t5("кіт").unwrap();
    assert_eq!(physical, [0x00, 0x15, 0x09, 0xa3, 0x7d]);
    let decoded = decode_ternary_words(&physical).unwrap();
    assert_eq!(decoded.len(), 3);
    assert_eq!(decoded.iter().map(|word| word.width()).collect::<Vec<_>>(), [7, 7, 7]);
    assert_eq!(
        decoded.iter().map(|word| word.packed_bits()).collect::<Vec<_>>(),
        [0, 68, 15],
    );
    assert_eq!(decode_d7_uk_t5(&physical).unwrap(), "кіт");
}

#[test]
fn uppercase_is_an_owner_ratified_modifier_not_a_fake_new_glyph() {
    let physical = encode_d7_uk_t5("Кіт").unwrap();
    let decoded = decode_ternary_words(&physical).unwrap();
    assert_eq!(decoded.iter().map(|w| w.packed_bits()).collect::<Vec<_>>(),
               [0x22, 0x00, 0x44, 0x0f]);
    assert!(decoded.iter().all(|w| w.width() == 7));
    assert_eq!(decode_d7_uk_t5(&physical).unwrap(), "Кіт");
}

#[test]
fn d2_is_structure_not_d7_text() {
    for glyph in [" ", "\t", "\n", "(", ")", "."] {
        assert!(matches!(
            encode_d7_uk_t5(glyph),
            Err(D7T5Error::UnassignedKeyboardGlyph { .. }),
        ), "D2 glyph leaked through D7: {glyph:?}");
    }
    for bits in [0b00, 0b01, 0b10, 0b11] {
        let byte = encode_ternary_words(&[
            BinarySourceWord::W2(Bit2::new(bits).unwrap())
        ]).unwrap();
        assert_eq!(decode_d7_uk_t5(&byte), Err(D7T5Error::NonD7Word));
    }
}

#[test]
fn historical_d7_duplicate_and_reserved_cells_fail_closed() {
    for bits in [0b1100000, 0b1100001, 0b1100010, 0b1100011, 0b1100100,
                 0b1111010, 0b0100001, 0b0101010] {
        let physical = encode_ternary_words(&[
            BinarySourceWord::W7(Bit7::new(bits).unwrap())
        ]).unwrap();
        assert_eq!(decode_d7_uk_t5(&physical),
                   Err(D7T5Error::UnrenderableD7Cell));
    }
}

#[test]
fn ukrainian_symbols_never_include_unassigned_ascii_or_sanskrit_transliteration() {
    for text in ["@", "#", "&", "<", ">", "k", "kh", "№", "я", "ї", "щ"] {
        assert!(matches!(encode_d7_uk_t5(text),
                         Err(D7T5Error::UnassignedKeyboardGlyph { .. })));
    }
    assert_eq!(decode_d7_uk_t5(&encode_d7_uk_t5("\"").unwrap()).unwrap(), "\"");
    assert_eq!(decode_d7_uk_t5(&encode_d7_uk_t5("'").unwrap()).unwrap(), "'");
}

#[test]
fn malformed_t5_does_not_fall_back_to_another_codec() {
    assert_eq!(decode_d7_uk_t5(&[243]),
               Err(D7T5Error::Transport(TernaryTransportError::InvalidPhysicalByte)));
}
