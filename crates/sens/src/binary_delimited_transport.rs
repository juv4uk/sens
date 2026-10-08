//! Альтернативний фізично ДВІЙКОВИЙ носій логічних 0/1/межа.
//!
//! Префіксний код: semantic 0 -> 0; semantic 1 -> 10; domain boundary -> 11.
//! Жоден з кодів не є префіксом іншого. '11' не виникає в data,
//! тож вихідні доменні біти не змінюються після відновлення.
//! Дві послідовні межі (1111) після завершеного слова — дослідний EOS.
//! Високі біти останнього байта — файл, а низькі до 7 бітів 0 — хвіст.
//! Це порівняльний транспорт до five-trits-per-byte, НЕ закон мови.

use crate::{BinarySourceWord, parse_binary_source_words, parse_canonical_binary};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BinaryDelimitedError {
    EmptyProgram,
    MissingEnd,
    InvalidWord,
    InvalidBinaryProjection,
    InvalidProgramSyntax,
    InvalidTail,
    TooLarge,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BinaryDelimitedAccounting {
    pub word_count: usize,
    pub semantic_bits: usize,
    pub ones_expansion_bits: usize,
    pub delimiter_bits: usize,
    pub eos_bits: usize,
    pub encoded_bits: usize,
    pub tail_bits: usize,
    pub physical_bits: usize,
    pub physical_bytes: usize,
}
const MAX_BYTES: usize = 4 * 1024 * 1024;

pub fn encode_binary_delimited_words(
    words: &[BinarySourceWord],
) -> Result<Vec<u8>, BinaryDelimitedError> {
    if words.is_empty() { return Err(BinaryDelimitedError::EmptyProgram); }
    let semantic_bits = words.iter().map(|w| w.width()).sum::<usize>();
    let ones = words.iter().map(|w| w.packed_bits().count_ones() as usize).sum::<usize>();
    let raw_len = semantic_bits + ones + (words.len() - 1) * 2 + 4;
    if raw_len.div_ceil(8) > MAX_BYTES { return Err(BinaryDelimitedError::TooLarge); }
    let mut output = Vec::with_capacity(raw_len.div_ceil(8));
    let mut current_byte = 0u8;
    let mut used = 0u8;

    let mut push_bit = |one: bool| {
        if one { current_byte |= 1 << (7 - used); }
        used += 1;
        if used == 8 {
            output.push(current_byte);
            current_byte = 0;
            used = 0;
        }
    };

    for (position, word) in words.iter().copied().enumerate() {
        if position > 0 {
            push_bit(true);
            push_bit(true);
        }
        let width = word.width();
        if !(1..=9).contains(&width) { return Err(BinaryDelimitedError::InvalidWord); }
        let raw = word.packed_bits();
        for shift in (0..width).rev() {
            if raw & (1 << shift) == 0 {
                push_bit(false);
            } else {
                push_bit(true);
                push_bit(false);
            }
        }
    }
    for _ in 0..4 { push_bit(true); } // EOS: 11 11
    if used > 0 { output.push(current_byte); }
    Ok(output)
}

/// Строгий самостійний декодер. Відновлює межі без .lisp і без width tags.
/// Експериментальний EOS=1111 та канонічні фінальні 0 відхиляють зайвий байт.
pub fn decode_binary_delimited_words(
    bytes: &[u8],
) -> Result<Vec<BinarySourceWord>, BinaryDelimitedError> {
    if bytes.is_empty() { return Err(BinaryDelimitedError::EmptyProgram); }
    if bytes.len() > MAX_BYTES { return Err(BinaryDelimitedError::TooLarge); }
    let count = bytes.len() * 8;
    let at = |i: usize| (bytes[i / 8] >> (7 - (i % 8))) & 1;
    let mut pos = 0;
    let mut word = String::new();
    let mut words = Vec::<String>::new();

    loop {
        if pos >= count { return Err(BinaryDelimitedError::MissingEnd); }
        if at(pos) == 0 {
            word.push('0');
            pos += 1;
        } else {
            if pos + 1 >= count { return Err(BinaryDelimitedError::MissingEnd); }
            let second = at(pos + 1);
            pos += 2;
            if second == 0 {
                word.push('1');
            } else if !word.is_empty() {
                words.push(std::mem::take(&mut word));
            } else {
                // Друга 11 після попередньої, це EOS, а НЕ семантичне слово.
                if words.is_empty() { return Err(BinaryDelimitedError::EmptyProgram); }
                if count - pos >= 8 || (pos..count).any(|i| at(i) != 0) {
                    return Err(BinaryDelimitedError::InvalidTail);
                }
                let projected = words.join(" ");
                let tokens = parse_binary_source_words(&projected)
                    .map_err(|_| BinaryDelimitedError::InvalidWord)?;
                let exact: Vec<_> = tokens.into_iter().map(|token| token.word).collect();
                if encode_binary_delimited_words(&exact)? != bytes {
                    return Err(BinaryDelimitedError::InvalidTail);
                }
                return Ok(exact);
            }
        }
        if word.len() > 9 { return Err(BinaryDelimitedError::InvalidWord); }
    }
}

pub fn encode_binary_delimited_projection(
    source: &str,
) -> Result<Vec<u8>, BinaryDelimitedError> {
    let tokens = parse_binary_source_words(source)
        .map_err(|_| BinaryDelimitedError::InvalidBinaryProjection)?;
    if tokens.is_empty() { return Err(BinaryDelimitedError::EmptyProgram); }
    parse_canonical_binary(source).map_err(|_| BinaryDelimitedError::InvalidProgramSyntax)?;
    encode_binary_delimited_words(&tokens.into_iter().map(|t| t.word).collect::<Vec<_>>())
}

pub fn decode_binary_delimited_program(
    bytes: &[u8],
) -> Result<Vec<BinarySourceWord>, BinaryDelimitedError> {
    let words = decode_binary_delimited_words(bytes)?;
    let projected = words.iter().map(ToString::to_string).collect::<Vec<_>>().join(" ");
    parse_canonical_binary(&projected).map_err(|_| BinaryDelimitedError::InvalidProgramSyntax)?;
    Ok(words)
}

pub fn binary_delimited_accounting(
    words: &[BinarySourceWord],
) -> Result<BinaryDelimitedAccounting, BinaryDelimitedError> {
    let bytes = encode_binary_delimited_words(words)?;
    let semantic_bits = words.iter().map(|w| w.width()).sum::<usize>();
    let ones_expansion_bits = words.iter().map(|w| w.packed_bits().count_ones() as usize).sum();
    let delimiter_bits = 2 * (words.len() - 1);
    let eos_bits = 4;
    let encoded_bits = semantic_bits + ones_expansion_bits + delimiter_bits + eos_bits;
    let physical_bits = bytes.len() * 8;
    Ok(BinaryDelimitedAccounting {
        word_count: words.len(), semantic_bits, ones_expansion_bits, delimiter_bits,
        eos_bits, encoded_bits, tail_bits: physical_bits - encoded_bits,
        physical_bits, physical_bytes: bytes.len(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    fn words(source: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(source).unwrap().into_iter().map(|w| w.word).collect()
    }

    #[test]
    fn five_words_roundtrip_without_third_physical_symbol() {
        let source = "10 001 00 000 01";
        let original = words(source);
        let physical = encode_binary_delimited_projection(source).unwrap();
        assert_eq!(decode_binary_delimited_program(&physical).unwrap(), original);
        let account = binary_delimited_accounting(&original).unwrap();
        assert_eq!(account.semantic_bits, 12);
        assert_eq!(account.ones_expansion_bits, 3);
        assert_eq!(account.delimiter_bits, 8);
        assert_eq!(account.eos_bits, 4);
        assert_eq!(account.encoded_bits, 27);
        assert_eq!(account.physical_bytes, 4);
        assert_eq!(account.tail_bits, 5);
    }

    #[test]
    fn previously_colliding_word_widths_have_distinct_physical_bytes() {
        let a = words("0 00");
        let b = words("000");
        let enc_a = encode_binary_delimited_words(&a).unwrap();
        let enc_b = encode_binary_delimited_words(&b).unwrap();
        assert_ne!(enc_a, enc_b);
        assert_eq!(decode_binary_delimited_words(&enc_a).unwrap(), a);
        assert_eq!(decode_binary_delimited_words(&enc_b).unwrap(), b);
    }

    #[test]
    fn all_possible_d1_to_d9_single_word_values_roundtrip() {
        for width in 1..=9 {
            for value in 0..(1 << width) {
                let source = format!("{value:0width$b}");
                let ws = words(&source);
                assert_eq!(decode_binary_delimited_words(
                    &encode_binary_delimited_words(&ws).unwrap()).unwrap(), ws);
            }
        }
    }

    #[test]
    fn payload_can_contain_d7_text_space_without_becoming_delimiter() {
        let ws = words("1100000 001 1100000");
        assert_eq!(decode_binary_delimited_words(
            &encode_binary_delimited_words(&ws).unwrap()).unwrap(), ws);
    }

    #[test]
    fn no_trailing_physical_bytes_or_mutated_tail() {
        let ws = words("10 001 00 000 01");
        let physical = encode_binary_delimited_words(&ws).unwrap();
        let mut extra = physical.clone();
        extra.push(0);
        assert_eq!(decode_binary_delimited_words(&extra), Err(BinaryDelimitedError::InvalidTail));
        let mut corrupted = physical.clone();
        *corrupted.last_mut().unwrap() |= 1;
        assert_eq!(decode_binary_delimited_words(&corrupted), Err(BinaryDelimitedError::InvalidTail));
    }

    #[test]
    fn never_accepts_early_or_missing_end() {
        assert_eq!(decode_binary_delimited_words(&[]), Err(BinaryDelimitedError::EmptyProgram));
        assert_eq!(decode_binary_delimited_words(&[0]), Err(BinaryDelimitedError::MissingEnd));
        assert_eq!(decode_binary_delimited_words(&[0xff]), Err(BinaryDelimitedError::EmptyProgram));
    }

    #[test]
    fn data_distribution_changes_best_transport_choice() {
        let zeros = words(&vec!["000000000"; 8].join(" "));
        let ones = words(&vec!["111111111"; 8].join(" "));
        let compact_zeros = encode_binary_delimited_words(&zeros).unwrap();
        let base3_zeros = crate::encode_ternary_words(&zeros).unwrap();
        assert!(compact_zeros.len() < base3_zeros.len());
        let compact_ones = encode_binary_delimited_words(&ones).unwrap();
        let base3_ones = crate::encode_ternary_words(&ones).unwrap();
        assert!(compact_ones.len() > base3_ones.len());
        assert_eq!(decode_binary_delimited_words(&compact_zeros).unwrap(), zeros);
        assert_eq!(decode_binary_delimited_words(&compact_ones).unwrap(), ones);
    }
}
