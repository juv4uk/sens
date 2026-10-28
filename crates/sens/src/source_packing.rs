//! ZIG-OWNED: physical bit-packing is the sterile Zig corridor's job (t5/f3c/transport.zig).
//! Rust is byte-addressed and must NOT pack: Zig hands it already-packed programs.
//! This module is retained only for the staged removal (#5617/#5609). Do not extend it.
//! Mechanical bridge from binary source words to the ZIG corridor.
//! ZIG-OWNED: the physical packing is the sterile Zig corridor's job (zig_transport / transport_abi.zig).
//! These functions delegate to the Zig ABI; Rust does not pack.
//!
//! This module assigns no semantic roles and defines no wire framing. It only
//! preserves source order while appending each exact-width word into one
//! continuous PackedBitstream.
//!
//! Important: a PackedBitstream preserves payload bits and total bit length,
//! not source word boundaries. Distinct exact-width source sequences can have
//! the same packed payload; a grammar or explicit framing layer must supply
//! widths when reconstruction requires them.

use crate::{
    domain_ladder::DomainCoordinate, BinarySourceToken, BinarySourceWord, BitPacker,
    PackedBitstream,
};

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

/// Pack exact D1–D10 coordinates with no interior byte padding.
///
/// Width is part of each validated coordinate. This operation does not infer
/// a domain from a numeric byte, assign callable semantics, or define a
/// standalone physical wire format; the decoder requires an external schedule.
pub fn pack_domain_coordinates(coordinates: &[DomainCoordinate]) -> PackedBitstream {
    let total_bits: usize = coordinates
        .iter()
        .map(|coordinate| usize::from(coordinate.width()))
        .sum();
    let mut packer = BitPacker::with_capacity_bits(total_bits);
    for &coordinate in coordinates {
        packer.push_coordinate(coordinate);
    }
    packer.finish()
}

/// Reconstruct exact D1–D10 coordinates using a caller-owned width schedule.
///
/// Reject invalid width, overflow, and incomplete or overlong schedules.
/// W8 and D8 remain separate identity types; this function never interprets
/// a byte as a historical function or a callable current resident.
pub fn unpack_domain_coordinates(
    packed: &PackedBitstream,
    widths: &[u8],
) -> Option<Vec<DomainCoordinate>> {
    let expected_bits = widths.iter().try_fold(0usize, |total, &width| {
        if !(1..=10).contains(&width) {
            return None;
        }
        total.checked_add(usize::from(width))
    })?;
    if expected_bits != packed.bit_len() {
        return None;
    }

    let mut coordinates = Vec::with_capacity(widths.len());
    let mut offset = 0usize;
    for &width in widths {
        coordinates.push(packed.read_coordinate(offset, width)?);
        offset += usize::from(width);
    }
    debug_assert_eq!(offset, packed.bit_len());
    Some(coordinates)
}

/// Append one already-bounded source word to the current dense payload.
///
/// Returns the starting bit offset of the word in the packed payload.
pub fn append_binary_source_word(packer: &mut BitPacker, word: BinarySourceWord) -> usize {
    // Width belongs to the already-validated source word, not the host u16.
    // Use the same bit-exact packer as D1–D10 without assigning any callability.
    let coordinate = DomainCoordinate::new(word.width() as u8, word.packed_bits())
        .expect("a bounded source fast-path word must fit its exact width");
    packer.push_coordinate(coordinate)
}

/// Count the exact semantic payload bits carried by canonical source tokens.
///
/// This function performs no semantic role lookup and invents no domain width.
/// Each token already carries its exact SENS source width; Rust only adds those
/// widths. Source whitespace/comments are absent from `tokens`, while D2
/// structural words remain ordinary exact-width source tokens and therefore
/// contribute their bits.
///
/// Wire framing and final-byte slack are intentionally excluded.
pub fn semantic_source_bits(tokens: &[BinarySourceToken]) -> usize {
    tokens.iter().map(|token| token.word.width()).sum()
}

/// Pack exact source words in program order with zero interior byte padding.
///
/// Source token spans and semantic word-boundary policy stay outside the packed
/// payload. The returned value is deliberately not self-describing with respect
/// to source word widths. Canonical wire/EOS and boundary metadata are owned
/// separately by framing work.
fn pack_source_words<I>(words: I, total_bits: usize) -> PackedBitstream
where
    I: IntoIterator<Item = BinarySourceWord>,
{
    let mut packer = BitPacker::with_capacity_bits(total_bits);
    for word in words {
        append_binary_source_word(&mut packer, word);
    }
    packer.finish()
}

/// Pack already-decoded exact-width words directly, without constructing a
/// visible zero/one source string or reparsing its tokens.
pub fn pack_binary_source_words(words: &[BinarySourceWord]) -> PackedBitstream {
    let total_bits = words.iter().map(|word| word.width()).sum();
    pack_source_words(words.iter().copied(), total_bits)
}

/// Pack exact source tokens in program order with zero interior byte padding.
/// This retains the source-token adapter for callers that already own spans.
pub fn pack_binary_source_tokens(tokens: &[BinarySourceToken]) -> PackedBitstream {
    pack_source_words(
        tokens.iter().map(|token| token.word),
        semantic_source_bits(tokens),
    )
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
        9 => BinarySourceWord::W9(packed.read_w9(bit_offset)?),
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
/// The decode fails closed if any width is outside 1..=9 or if the supplied
/// widths do not consume the payload bit length exactly.
pub fn unpack_binary_source_words(
    packed: &PackedBitstream,
    widths: &[usize],
) -> Option<Vec<BinarySourceWord>> {
    let expected_bits = widths.iter().try_fold(0usize, |total, &width| {
        if !(1..=9).contains(&width) {
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

