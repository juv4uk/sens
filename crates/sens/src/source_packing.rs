//! Mechanical bridge from already-tokenized binary source words to the dense
//! sequential bit packer.
//!
//! This module assigns no semantic roles and defines no wire framing. It only
//! preserves source order while appending each exact-width word into one
//! continuous PackedBitstream.
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

fn read_binary_source_word(
    packed: &PackedBitstream,
    bit_offset: usize,
    width: usize,
) -> Option<BinarySourceWord> {
    Some(match width {
        1 => BinarySourceWord::W1(packed.read::<1>(bit_offset)?),
        2 => BinarySourceWord::W2(packed.read::<2>(bit_offset)?),
        3 => BinarySourceWord::W3(packed.read::<3>(bit_offset)?),
        4 => BinarySourceWord::W4(packed.read::<4>(bit_offset)?),
        5 => BinarySourceWord::W5(packed.read::<5>(bit_offset)?),
        6 => BinarySourceWord::W6(packed.read::<6>(bit_offset)?),
        7 => BinarySourceWord::W7(packed.read::<7>(bit_offset)?),
        8 => BinarySourceWord::W8(packed.read::<8>(bit_offset)?),
        _ => return None,
    })
}

/// Reconstruct exact source words from a dense payload when the caller already
/// owns the exact word-width schedule.
///
/// This is deliberately grammar/domain-bound mechanics, not a standalone wire
/// decoder and not semantic dispatch. Equal-total alternative width schedules
/// can describe the same raw payload bits, so `widths` is explicit
/// caller-owned boundary information. Standalone self-description belongs to
/// the framing layer.
///
/// The decode fails closed if any width is outside 1..=8 or if the supplied
/// widths do not consume the payload bit length exactly.
pub fn unpack_binary_source_words(
    packed: &PackedBitstream,
    widths: &[usize],
) -> Option<Vec<BinarySourceWord>> {
    let expected_bits = widths.iter().try_fold(0usize, |total, &width| {
        if !(1..=8).contains(&width) {
            return None;
        }
        total.checked_add(width)
    })?;

    if expected_bits != packed.bit_len() {
        return None;
    }

    let mut words = Vec::with_capacity(widths.len());
    let mut bit_offset = 0usize;

    for &width in widths {
        words.push(read_binary_source_word(packed, bit_offset, width)?);
        bit_offset += width;
    }

    debug_assert_eq!(bit_offset, packed.bit_len());
    Some(words)
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
    fn exact_domain_widths_do_not_expand_to_host_bytes() {
        let d5 = parse_binary_source_words(
            "00000 00001 00010 00011 00100 00101 00110 00111"
        ).unwrap();
        let d6 = parse_binary_source_words(
            "000000 000001 000010 000011"
        ).unwrap();
        let d7 = parse_binary_source_words(
            "0000000 0000001 0000010 0000011 0000100 0000101 0000110 0000111"
        ).unwrap();

        let packed_d5 = pack_binary_source_tokens(&d5);
        let packed_d6 = pack_binary_source_tokens(&d6);
        let packed_d7 = pack_binary_source_tokens(&d7);

        // Semantic width is the domain width, regardless of the host carrier.
        assert_eq!(packed_d5.bit_len(), 8 * 5);
        assert_eq!(packed_d5.byte_len(), 5);

        assert_eq!(packed_d6.bit_len(), 4 * 6);
        assert_eq!(packed_d6.byte_len(), 3);

        assert_eq!(packed_d7.bit_len(), 8 * 7);
        assert_eq!(packed_d7.byte_len(), 7);

        // These examples end exactly on a byte boundary, so the physical
        // container contributes no tail bits at all.
        assert_eq!(packed_d5.valid_bits_in_last_byte(), 8);
        assert_eq!(packed_d6.valid_bits_in_last_byte(), 8);
        assert_eq!(packed_d7.valid_bits_in_last_byte(), 8);
    }

    #[test]
    fn canonical_mixed_example_counts_bits_not_words_or_host_objects() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(
            tokens.iter().map(|token| token.word.width()).sum::<usize>(),
            2 + 3 + 2
        );
        assert_eq!(packed.bit_len(), 7);
        assert_eq!(packed.byte_len(), 1);
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

    fn exact_words(tokens: &[BinarySourceToken]) -> Vec<BinarySourceWord> {
        tokens.iter().map(|token| token.word).collect()
    }

    fn assert_grammar_bound_round_trip(source: &str) {
        let tokens = parse_binary_source_words(source).unwrap();
        let widths: Vec<_> = tokens.iter().map(|token| token.word.width()).collect();
        let packed = pack_binary_source_tokens(&tokens);

        let decoded = unpack_binary_source_words(&packed, &widths).expect("exact widths decode");
        assert_eq!(decoded, exact_words(&tokens));
    }

    #[test]
    fn grammar_bound_decoder_round_trips_canonical_example() {
        assert_grammar_bound_round_trip("10 001 01");
    }

    #[test]
    fn grammar_bound_decoder_preserves_width_anti_collapse() {
        assert_grammar_bound_round_trip("1 01 001 0001");
    }

    #[test]
    fn grammar_bound_decoder_handles_cross_byte_and_all_widths() {
        assert_grammar_bound_round_trip("1111111 101");
        assert_grammar_bound_round_trip("1 10 101 1010 10101 101010 1010101 10101010");
    }

    #[test]
    fn grammar_bound_decoder_rejects_invalid_or_non_exact_total_widths() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert!(unpack_binary_source_words(&packed, &[0, 3, 2]).is_none());
        assert!(unpack_binary_source_words(&packed, &[9]).is_none());
        assert!(unpack_binary_source_words(&packed, &[2, 3]).is_none());
        assert!(unpack_binary_source_words(&packed, &[2, 3, 3]).is_none());
    }

    #[test]
    fn equal_total_width_schedule_is_explicit_caller_owned_information() {
        let split = parse_binary_source_words("0 00").unwrap();
        let single = parse_binary_source_words("000").unwrap();
        let packed = pack_binary_source_tokens(&split);

        assert!(packed == pack_binary_source_tokens(&single));
        assert_eq!(
            unpack_binary_source_words(&packed, &[1, 2]).unwrap(),
            exact_words(&split)
        );
        assert_eq!(
            unpack_binary_source_words(&packed, &[3]).unwrap(),
            exact_words(&single)
        );
    }

    #[test]
    fn comments_and_whitespace_do_not_consume_payload_bits() {
        let tokens = parse_binary_source_words("10 ; open\n 001\t01 ; close\n").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(packed.bit_len(), 7);
        assert_eq!(packed.bytes(), &[0b1000_1010]);
    }
}
