//! #2766 — mechanical D5 exact-width source boundary witness.
//!
//! This proves only representation/source-boundary support for all 32 exact
//! five-bit words. It does not claim semantic residency, registry admission,
//! lowering or evaluator dispatch.

use sens::{parse_binary_source_words, BinarySourceWord, Bit1, Bit2, Bit3, Bit4, Bit6, Bit7, Bit8, CoreD5Word};
use std::mem::size_of;

#[test]
fn every_exact_d5_word_round_trips_as_w5_without_padding() {
    for raw in 0u8..32 {
        let source = format!("{raw:05b}");
        let tokens = parse_binary_source_words(&source).expect("exact D5 source word");
        assert_eq!(tokens.len(), 1);

        let word = tokens[0].word;
        assert_eq!(word.width(), 5);
        assert_eq!(word.packed_bits(), raw);
        assert_eq!(word.to_string(), source);
        assert!(matches!(word, BinarySourceWord::W5(_)));
    }
}


#[test]
fn every_w5_word_round_trips_through_core_d5_without_sens8_widening() {
    for raw in 0u8..32 {
        let source = format!("{raw:05b}");
        let tokens = parse_binary_source_words(&source).expect("exact D5 source word");
        let word = tokens[0].word;

        let typed: CoreD5Word = word.core_d5().expect("W5 must enter Core.D5");
        assert_eq!(typed.word().packed_bits(), raw);

        let roundtrip = BinarySourceWord::from(typed);
        assert_eq!(roundtrip, word);
        assert_eq!(roundtrip.width(), 5);
        assert_eq!(roundtrip.to_string(), source);
    }

    assert_eq!(size_of::<CoreD5Word>(), 1);
}

#[test]
fn non_w5_words_fail_closed_at_core_d5_bridge() {
    for source in [
        BinarySourceWord::W1(Bit1::new(0).unwrap()),
        BinarySourceWord::W2(Bit2::new(0).unwrap()),
        BinarySourceWord::W3(Bit3::new(0).unwrap()),
        BinarySourceWord::W4(Bit4::new(0).unwrap()),
        BinarySourceWord::W6(Bit6::new(0).unwrap()),
        BinarySourceWord::W7(Bit7::new(0).unwrap()),
        BinarySourceWord::W8(Bit8::new(0).unwrap()),
    ] {
        assert!(source.core_d5().is_none());
    }
}
