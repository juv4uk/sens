//! Research-only, HDLC-like bit-stuffing candidate for domain word boundaries.
//!
//! This is NOT the PPP protocol and NOT a ratified SENS file format.
//! Each word gets its own flag; 01111110 never occurs in stuffed data.
//! Syntax: FLAG word1 FLAG ... wordN FLAG FLAG, final repeated flag = EOS.
//! Byte container pads its last octet with zero bits, verified by re-encode.
//! Using one flag only around an entire program cannot delimit domain words.
//! RFC 1662 bit stuffing: insert 0 after every FIVE consecutive data ones.

use crate::{parse_binary_source_words, BinarySourceWord};

const FLAG: [u8; 8] = [0, 1, 1, 1, 1, 1, 1, 0];
const MAX_BYTES: usize = 4 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HdlcProbeError {
    EmptyProgram,
    MissingInitialFlag,
    MissingEndFlag,
    EmptyWord,
    InvalidStuffedPayload,
    InvalidWord,
    NoncanonicalTail,
    TooLarge,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HdlcProbeAccounting {
    pub word_count: usize,
    pub semantic_bits: usize,
    pub flag_bits: usize,
    pub stuffed_bits: usize,
    pub encoded_bits: usize,
    pub tail_bits: usize,
    pub physical_bytes: usize,
}

fn push_flag(bits: &mut Vec<u8>) {
    bits.extend_from_slice(&FLAG);
}

fn as_bytes(bits: &[u8]) -> Vec<u8> {
    let mut out = vec![0u8; bits.len().div_ceil(8)];
    for (i, b) in bits.iter().copied().enumerate() {
        if b == 1 { out[i / 8] |= 1 << (7 - i % 8); }
    }
    out
}

pub fn encode_hdlc_probe_words(
    words: &[BinarySourceWord],
) -> Result<Vec<u8>, HdlcProbeError> {
    if words.is_empty() { return Err(HdlcProbeError::EmptyProgram); }
    let semantic_bits = words.iter().map(|w| w.width()).sum::<usize>();
    let capacity = semantic_bits + words.len().saturating_add(2).saturating_mul(8)
        + semantic_bits.div_ceil(5);
    if capacity.div_ceil(8) > MAX_BYTES { return Err(HdlcProbeError::TooLarge); }
    let mut bits = Vec::with_capacity(capacity);
    push_flag(&mut bits);
    for word in words {
        let width = word.width();
        if !(1..=9).contains(&width) { return Err(HdlcProbeError::InvalidWord); }
        let mut ones = 0;
        let data = word.packed_bits();
        for shift in (0..width).rev() {
            let bit = ((data >> shift) & 1) as u8;
            bits.push(bit);
            if bit == 1 {
                ones += 1;
                if ones == 5 {
                    bits.push(0);
                    ones = 0;
                }
            } else {
                ones = 0;
            }
        }
        push_flag(&mut bits);
    }
    push_flag(&mut bits); // End-of-stream is a second flag with no intervening word.
    Ok(as_bytes(&bits))
}

fn bit_at(bytes: &[u8], index: usize) -> u8 {
    (bytes[index / 8] >> (7 - index % 8)) & 1
}

fn is_flag(bytes: &[u8], index: usize) -> bool {
    index + 8 <= bytes.len() * 8
        && FLAG.iter().enumerate().all(|(i,b)| bit_at(bytes, index + i) == *b)
}

fn unstuff_one_word(
    bytes: &[u8], start: usize, end: usize,
) -> Result<String, HdlcProbeError> {
    let mut word = String::new();
    let mut pos = start;
    let mut consecutive_ones = 0;
    while pos < end {
        let bit = bit_at(bytes, pos);
        pos += 1;
        word.push(if bit == 0 { '0' } else { '1' });
        if bit == 0 { consecutive_ones = 0; }
        else {
            consecutive_ones += 1;
            if consecutive_ones == 5 {
                if pos >= end || bit_at(bytes, pos) != 0 {
                    return Err(HdlcProbeError::InvalidStuffedPayload);
                }
                pos += 1;
                consecutive_ones = 0;
            }
        }
        if word.len() > 9 { return Err(HdlcProbeError::InvalidWord); }
    }
    if word.is_empty() { return Err(HdlcProbeError::EmptyWord); }
    Ok(word)
}

pub fn decode_hdlc_probe_words(
    bytes: &[u8],
) -> Result<Vec<BinarySourceWord>, HdlcProbeError> {
    if bytes.is_empty() { return Err(HdlcProbeError::EmptyProgram); }
    if bytes.len() > MAX_BYTES { return Err(HdlcProbeError::TooLarge); }
    if !is_flag(bytes, 0) { return Err(HdlcProbeError::MissingInitialFlag); }

    let size = bytes.len() * 8;
    let mut pos = 8;
    let mut parts = Vec::<String>::new();
    loop {
        let next = (pos..size.saturating_sub(7))
            .find(|offset| is_flag(bytes, *offset))
            .ok_or(HdlcProbeError::MissingEndFlag)?;
        if next == pos {
            // Empty segment is ONLY legal for the final repeated flag.
            if parts.is_empty() { return Err(HdlcProbeError::EmptyProgram); }
            let final_pos = next + 8;
            if size - final_pos >= 8
                || (final_pos..size).any(|i| bit_at(bytes, i) != 0)
            { return Err(HdlcProbeError::NoncanonicalTail); }
            let tokens = parse_binary_source_words(&parts.join(" "))
                .map_err(|_| HdlcProbeError::InvalidWord)?;
            let words: Vec<_> = tokens.into_iter().map(|t| t.word).collect();
            // Detect alternate spellings and ambiguous padding/truncation.
            if encode_hdlc_probe_words(&words)? != bytes {
                return Err(HdlcProbeError::NoncanonicalTail);
            }
            return Ok(words);
        }
        parts.push(unstuff_one_word(bytes, pos, next)?);
        pos = next + 8;
    }
}

pub fn hdlc_probe_accounting(
    words: &[BinarySourceWord],
) -> Result<HdlcProbeAccounting, HdlcProbeError> {
    let bytes = encode_hdlc_probe_words(words)?;
    let semantic_bits = words.iter().map(|w| w.width()).sum::<usize>();
    let stuffed_bits: usize = words.iter().map(|w| {
        let mut consecutive_ones = 0usize;
        let mut inserted = 0usize;
        for shift in (0..w.width()).rev() {
            if (w.packed_bits() >> shift) & 1 == 1 {
                consecutive_ones += 1;
                if consecutive_ones == 5 { inserted += 1; consecutive_ones = 0; }
            } else { consecutive_ones = 0; }
        }
        inserted
    }).sum();
    let flag_bits = (words.len() + 2) * 8;
    let encoded_bits = semantic_bits + flag_bits + stuffed_bits;
    Ok(HdlcProbeAccounting {
        word_count: words.len(),
        semantic_bits, flag_bits, stuffed_bits, encoded_bits,
        tail_bits: bytes.len() * 8 - encoded_bits,
        physical_bytes: bytes.len(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn words(s: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(s).unwrap()
            .into_iter().map(|token| token.word).collect()
    }

    #[test]
    fn five_words_roundtrip_with_explicit_word_boundary_flags() {
        let input = words("10 001 00 000 01");
        let raw = encode_hdlc_probe_words(&input).unwrap();
        assert_eq!(decode_hdlc_probe_words(&raw).unwrap(), input);
        let measured = hdlc_probe_accounting(&input).unwrap();
        assert_eq!((measured.semantic_bits, measured.flag_bits,
                    measured.stuffed_bits), (12, 56, 0));
        assert_eq!(measured.encoded_bits, 68);
        assert_eq!(measured.physical_bytes, 9);
        assert_eq!(measured.tail_bits, 4);
        // Both previous research candidates fit this case in four bytes.
        assert_eq!(crate::encode_ternary_words(&input).unwrap().len(), 4);
        assert_eq!(crate::encode_binary_delimited_words(&input).unwrap().len(), 4);
    }

    #[test]
    fn stuffed_zero_after_five_ones_cannot_masquerade_as_flag() {
        let input = words("111111111 111110 11111");
        let wire = encode_hdlc_probe_words(&input).unwrap();
        let stats = hdlc_probe_accounting(&input).unwrap();
        assert_eq!(stats.stuffed_bits, 3);
        assert_eq!(decode_hdlc_probe_words(&wire).unwrap(), input);
    }

    #[test]
    fn naked_collision_is_separated_without_altering_d1_or_d3() {
        let a = words("0 00");
        let b = words("000");
        let ea = encode_hdlc_probe_words(&a).unwrap();
        let eb = encode_hdlc_probe_words(&b).unwrap();
        assert_ne!(ea, eb);
        assert_eq!(decode_hdlc_probe_words(&ea).unwrap(), a);
        assert_eq!(decode_hdlc_probe_words(&eb).unwrap(), b);
    }

    #[test]
    fn all_single_words_d1_to_d9_roundtrip() {
        for width in 1..=9 {
            for value in 0..(1usize << width) {
                let input = words(&format!("{value:0width$b}"));
                let data = encode_hdlc_probe_words(&input).unwrap();
                assert_eq!(decode_hdlc_probe_words(&data).unwrap(), input);
            }
        }
    }

    #[test]
    fn no_extra_byte_or_noncanonical_tail() {
        let input = words("10 001 00 000 01");
        let raw = encode_hdlc_probe_words(&input).unwrap();
        let mut appended = raw.clone();
        appended.push(0);
        assert_eq!(decode_hdlc_probe_words(&appended),
                   Err(HdlcProbeError::NoncanonicalTail));
        let mut changed = raw;
        *changed.last_mut().unwrap() |= 1;
        assert_eq!(decode_hdlc_probe_words(&changed),
                   Err(HdlcProbeError::NoncanonicalTail));
    }

    #[test]
    fn require_a_real_eos_not_just_end_of_physical_bytes() {
        assert_eq!(decode_hdlc_probe_words(&[]),
                   Err(HdlcProbeError::EmptyProgram));
        assert_eq!(decode_hdlc_probe_words(&[0]),
                   Err(HdlcProbeError::MissingInitialFlag));
        let input = words("000");
        let mut bytes = encode_hdlc_probe_words(&input).unwrap();
        bytes.truncate(1);
        assert_eq!(decode_hdlc_probe_words(&bytes),
                   Err(HdlcProbeError::MissingEndFlag));
    }
}
