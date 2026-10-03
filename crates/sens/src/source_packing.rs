//! Mechanical bridge from already-tokenized binary source words to the dense
//! sequential bit packer, and the inverse under an explicit width schedule.
//!
//! This module assigns no semantic roles and defines no wire framing. It only
//! preserves source order while appending each exact-width word into one
//! continuous PackedBitstream, or reconstructs words when the caller supplies
//! exact widths.
//!
//! Important: a PackedBitstream preserves payload bits and total bit length,
//! not source word boundaries. Distinct exact-width source sequences can have
//! the same packed payload; a grammar or explicit framing layer must supply
//! widths when reconstruction requires them.

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
/// payload. The returned value is deliberately not self-describing with respect
/// to source word widths. Canonical wire/EOS and boundary metadata are owned
/// separately by framing work.
pub fn pack_binary_source_tokens(tokens: &[BinarySourceToken]) -> PackedBitstream {
    let total_bits = tokens.iter().map(|token| token.word.width()).sum();
    let mut packer = BitPacker::with_capacity_bits(total_bits);

    for token in tokens {
        append_binary_source_word(&mut packer, token.word);
    }

    packer.finish()
}

/// Grammar-bound inverse of [`pack_binary_source_tokens`].
///
/// Reads exact-width words from a canonical [`PackedBitstream`] using a caller-
/// supplied width schedule (1..=8). Fails closed when any width is invalid, a
/// read would cross `bit_len`, or the widths do not consume **exactly**
/// `bit_len` bits.
///
/// Equal-total alternative schedules remain grammar-owned: this function does
/// not invent boundaries from the payload alone.
pub fn unpack_binary_source_words(
    packed: &PackedBitstream,
    widths: &[usize],
) -> Option<Vec<BinarySourceWord>> {
    let mut offset = 0usize;
    let mut out = Vec::with_capacity(widths.len());

    for &width in widths {
        if width == 0 || width > 8 {
            return None;
        }

        let word = read_source_word(packed, offset, width)?;
        offset = offset.checked_add(width)?;
        out.push(word);
    }

    if offset != packed.bit_len() {
        return None;
    }

    Some(out)
}

fn read_source_word(
    packed: &PackedBitstream,
    offset: usize,
    width: usize,
) -> Option<BinarySourceWord> {
    match width {
        1 => packed.read::<1>(offset).map(BinarySourceWord::W1),
        2 => packed.read::<2>(offset).map(BinarySourceWord::W2),
        3 => packed.read::<3>(offset).map(BinarySourceWord::W3),
        4 => packed.read::<4>(offset).map(BinarySourceWord::W4),
        5 => packed.read::<5>(offset).map(BinarySourceWord::W5),
        6 => packed.read::<6>(offset).map(BinarySourceWord::W6),
        7 => packed.read::<7>(offset).map(BinarySourceWord::W7),
        8 => packed.read::<8>(offset).map(BinarySourceWord::W8),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse_binary_source_words;

    fn widths_of(tokens: &[BinarySourceToken]) -> Vec<usize> {
        tokens.iter().map(|token| token.word.width()).collect()
    }

    fn words_of(tokens: &[BinarySourceToken]) -> Vec<BinarySourceWord> {
        tokens.iter().map(|token| token.word).collect()
    }

    #[test]
    fn canonical_source_example_becomes_one_dense_seven_bit_payload() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(packed.bit_len(), 7);
        assert_eq!(packed.byte_len(), 1);
        assert_eq!(packed.bytes(), &[0b1000_1010]);
    }

    #[test]
    fn canonical_example_round_trips_under_explicit_widths() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);
        let decoded = unpack_binary_source_words(&packed, &widths_of(&tokens)).unwrap();

        assert_eq!(decoded, words_of(&tokens));
        assert_eq!(
            decoded.iter().map(|word| word.width()).collect::<Vec<_>>(),
            [2, 3, 2]
        );
    }

    #[test]
    fn anti_collapse_sequence_round_trips() {
        let tokens = parse_binary_source_words("1 01 001 0001").unwrap();
        let packed = pack_binary_source_tokens(&tokens);
        let decoded = unpack_binary_source_words(&packed, &widths_of(&tokens)).unwrap();
        assert_eq!(decoded, words_of(&tokens));
    }

    #[test]
    fn word_crossing_byte_boundary_round_trips() {
        let tokens = parse_binary_source_words("1111111 101").unwrap();
        let packed = pack_binary_source_tokens(&tokens);
        let decoded = unpack_binary_source_words(&packed, &widths_of(&tokens)).unwrap();
        assert_eq!(decoded, words_of(&tokens));
    }

    #[test]
    fn all_widths_one_to_eight_round_trip_in_one_sequence() {
        let tokens =
            parse_binary_source_words("1 10 101 1010 10101 101010 1010101 10101010").unwrap();
        let packed = pack_binary_source_tokens(&tokens);
        let decoded = unpack_binary_source_words(&packed, &widths_of(&tokens)).unwrap();
        assert_eq!(decoded, words_of(&tokens));
    }

    #[test]
    fn invalid_width_rejects() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);
        assert!(unpack_binary_source_words(&packed, &[2, 0, 2]).is_none());
        assert!(unpack_binary_source_words(&packed, &[2, 9]).is_none());
    }

    #[test]
    fn non_exact_total_bit_consumption_rejects() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);
        assert!(unpack_binary_source_words(&packed, &[2, 3]).is_none());
        assert!(unpack_binary_source_words(&packed, &[2, 3, 2, 1]).is_none());
    }

    #[test]
    fn equal_total_alternative_schedules_are_grammar_owned() {
        let split = parse_binary_source_words("0 00").unwrap();
        let single = parse_binary_source_words("000").unwrap();
        let packed = pack_binary_source_tokens(&split);

        let as_split = unpack_binary_source_words(&packed, &[1, 2]).unwrap();
        let as_single = unpack_binary_source_words(&packed, &[3]).unwrap();

        assert_eq!(as_split, words_of(&split));
        assert_eq!(as_single, words_of(&single));
        assert_ne!(as_split, as_single);
    }

    #[test]
    fn append_records_crossing_offsets_for_w3_after_seven_bits() {
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
        assert_eq!(
            packed.bytes(),
            &[0b1101_0110, 0b1010_1011, 0b0101_0101, 0b0101_1010, 0b1010_0000]
        );
    }

    #[test]
    fn packed_payload_does_not_claim_source_word_boundaries() {
        let split = parse_binary_source_words("0 00").unwrap();
        let single = parse_binary_source_words("000").unwrap();

        assert_eq!(
            split.iter().map(|token| token.word.width()).collect::<Vec<_>>(),
            [1, 2]
        );
        assert_eq!(
            single.iter().map(|token| token.word.width()).collect::<Vec<_>>(),
            [3]
        );

        let split_packed = pack_binary_source_tokens(&split);
        let single_packed = pack_binary_source_tokens(&single);

        assert_eq!(split_packed.bit_len(), 3);
        assert_eq!(single_packed.bit_len(), 3);
        assert_eq!(split_packed.bytes(), single_packed.bytes());
        assert_eq!(split_packed.bytes(), &[0b0000_0000]);
    }

    #[test]
    fn comments_and_whitespace_do_not_consume_payload_bits() {
        let tokens = parse_binary_source_words("10 ; open\n 001\t01 ; close\n").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(packed.bit_len(), 7);
        assert_eq!(packed.bytes(), &[0b1000_1010]);
    }
}
