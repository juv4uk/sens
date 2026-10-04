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

/// Accounting for one canonical densely-packed semantic payload.
///
/// The payload carries only exact semantic bits. `framing_bits` is supplied by
/// the caller because grammar/EOS/container framing is a separate protocol
/// concern. `tail_unused_bits` is physical byte-container slack only; it is
/// never semantic padding and never appears between words.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PackedTransportAccounting {
    pub semantic_payload_bits: usize,
    pub framing_bits: usize,
    pub tail_unused_bits: usize,
    pub total_wire_bits: usize,
}

impl PackedTransportAccounting {
    /// Fraction of physical wire bits that are semantic payload.
    ///
    /// Empty transport has no utilization ratio.
    pub fn utilization(self) -> Option<f64> {
        (self.total_wire_bits != 0)
            .then(|| self.semantic_payload_bits as f64 / self.total_wire_bits as f64)
    }
}

/// Report semantic payload, external framing and final physical-byte slack
/// independently.
///
/// This function deliberately does not invent a width schedule or framing
/// format. A caller that already owns grammar/context can pass `framing_bits=0`;
/// a standalone container can pass its independently-accounted framing cost.
pub fn packed_transport_accounting(
    packed: &PackedBitstream,
    framing_bits: usize,
) -> PackedTransportAccounting {
    let physical_payload_bits = packed.byte_len() * 8;
    let tail_unused_bits = physical_payload_bits - packed.bit_len();
    PackedTransportAccounting {
        semantic_payload_bits: packed.bit_len(),
        framing_bits,
        tail_unused_bits,
        total_wire_bits: physical_payload_bits + framing_bits,
    }
}

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
    fn canonical_transport_accounting_keeps_payload_framing_and_tail_separate() {
        let tokens = parse_binary_source_words("10 001 01").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        let grammar_bound = packed_transport_accounting(&packed, 0);
        assert_eq!(
            grammar_bound,
            PackedTransportAccounting {
                semantic_payload_bits: 7,
                framing_bits: 0,
                tail_unused_bits: 1,
                total_wire_bits: 8,
            }
        );
        assert_eq!(grammar_bound.utilization(), Some(7.0 / 8.0));

        let standalone = packed_transport_accounting(&packed, 5);
        assert_eq!(standalone.semantic_payload_bits, 7);
        assert_eq!(standalone.framing_bits, 5);
        assert_eq!(standalone.tail_unused_bits, 1);
        assert_eq!(standalone.total_wire_bits, 13);
        assert_eq!(standalone.utilization(), Some(7.0 / 13.0));
    }

    #[test]
    fn homogeneous_exact_width_blocks_pay_no_interior_or_tail_padding() {
        for (source, expected_bits, expected_bytes) in [
            ("10101 10101 10101 10101 10101 10101 10101 10101", 40, 5),
            ("101010 101010 101010 101010", 24, 3),
            ("1010101 1010101 1010101 1010101 1010101 1010101 1010101 1010101", 56, 7),
        ] {
            let tokens = parse_binary_source_words(source).unwrap();
            let packed = pack_binary_source_tokens(&tokens);
            let accounting = packed_transport_accounting(&packed, 0);

            assert_eq!(accounting.semantic_payload_bits, expected_bits);
            assert_eq!(packed.byte_len(), expected_bytes);
            assert_eq!(accounting.tail_unused_bits, 0);
            assert_eq!(accounting.total_wire_bits, expected_bits);
            assert_eq!(accounting.utilization(), Some(1.0));
        }
    }

    #[test]
    fn comments_and_whitespace_do_not_consume_payload_bits() {
        let tokens = parse_binary_source_words("10 ; open\n 001\t01 ; close\n").unwrap();
        let packed = pack_binary_source_tokens(&tokens);

        assert_eq!(packed.bit_len(), 7);
        assert_eq!(packed.bytes(), &[0b1000_1010]);
    }
}
