//! Mechanical bridge from already-tokenized binary source words to the dense
//! sequential bit packer.
//!
//! This module assigns no semantic roles and defines no wire framing. It only
//! preserves source order while appending each exact-width word into one
//! continuous PackedBitstream.

use crate::{BinarySourceToken, BinarySourceWord, BitPacker, PackedBitstream};

/// Append one already-bounded source word to the current dense payload.
///
/// Returns the starting bit offset of the word in the packed payload.
pub fn append_binary_source_word(packer: &mut BitPacker, word: BinarySourceWord) -> usize {
    match word {
        BinarySourceWord::W1(word) => packer.push(word),
        BinarySourceWord::W2(word) => packer.push(word),
        BinarySourceWord::W3(word) => packer.push(word),
        BinarySourceWord::W4(word) => packer.push(word),
        BinarySourceWord::W5(word) => packer.push(word),
        BinarySourceWord::W6(word) => packer.push(word),
        BinarySourceWord::W7(word) => packer.push(word),
        BinarySourceWord::W8(word) => packer.push(word),
    }
}

/// Pack exact source words in program order with zero interior byte padding.
///
/// Source token spans and semantic word-boundary policy stay outside the packed
/// payload. Canonical wire/EOS metadata is owned separately by framing work.
pub fn pack_binary_source_tokens(tokens: &[BinarySourceToken]) -> PackedBitstream {
    let total_bits = tokens.iter().map(|token| token.word.width()).sum();
    let mut packer = BitPacker::with_capacity_bits(total_bits);

    for token in tokens {
        append_binary_source_word(&mut packer, token.word);
    }

    packer.finish()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse_binary_source_words;

    #[test]
    fn canonical_source_example_becomes_one_dense_seven_bit_payload() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(packed.bit_len(), 7);
        assert_eq!(packed.byte_len(), 1);
        assert_eq!(packed.bytes(), &[0b1000_1010]);
        assert_eq!(packed.valid_bits_in_last_byte(), 7);
    }

    #[test]
    fn equal_numeric_values_at_distinct_source_widths_pack_without_alignment() {
        let tokens = parse_binary_source_words("1 01 001 0001").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(tokens.iter().map(|t| t.word.width()).collect::<Vec<_>>(), [1, 2, 3, 4]);
        assert_eq!(packed.bit_len(), 10);
        assert_eq!(packed.bytes(), &[0b1010_0100, 0b0100_0000]);
    }

    #[test]
    fn source_word_may_cross_physical_byte_boundary() {
        let tokens = parse_binary_source_words("1111111 101").unwrap();
        let mut packer = BitPacker::new();

        let first = append_binary_source_word(&mut packer, tokens[0].word);
        let crossing = append_binary_source_word(&mut packer, tokens[1].word);
        let packed = packer.finish();

        assert_eq!(first, 0);
        assert_eq!(crossing, 7);
        assert_eq!(packed.bit_len(), 10);
        assert_eq!(packed.bytes(), &[0b1111_1111, 0b0100_0000]);
    }

    #[test]
    fn structural_bit_patterns_are_packed_as_payload_not_transport_delimiters() {
        let tokens = parse_binary_source_words("00 01 10 11").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(packed.bit_len(), 8);
        assert_eq!(packed.bytes(), &[0b0001_1011]);
    }

    #[test]
    fn mixed_widths_one_to_eight_reach_the_payload_lower_bound() {
        let tokens =
            parse_binary_source_words("1 10 101 1010 10101 101010 1010101 10101010").unwrap();
        let payload_bits: usize = tokens.iter().map(|token| token.word.width()).sum();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(payload_bits, 36);
        assert_eq!(packed.bit_len(), payload_bits);
        assert_eq!(packed.byte_len(), payload_bits.div_ceil(8));
        assert_eq!(packed.bytes(), &[0b1101_0110, 0b1010_1011, 0b0101_0101, 0b0101_1010, 0b1010_0000]);
    }

    #[test]
    fn comments_and_whitespace_do_not_consume_payload_bits() {
        let tokens = parse_binary_source_words("10 ; open\n 001\t01 ; close\n").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(packed.bit_len(), 7);
        assert_eq!(packed.bytes(), &[0b1000_1010]);
    }
}
