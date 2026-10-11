//! RESEARCH ONLY: D2-optimized prefix tags for exact binary SENS source words.
//!
//! No inter-word separator. This physical codec distinguishes exact width by
//! a prefix-free tag, preserving the *existing* D2 structural codes intact:
//! D2 => 0; D1,D3...D9 => 1000,1001,...1111.
//! A gamma-coded word count controls EOF and canonical zero byte padding.
//! All count/tag/padding bits are transport overhead, NOT bits of SENS.
//! Note: preserving source words is stricter than AST equivalence; the
//! source reader may semantically ignore D2 00, but deletion changes the
//! exact binary source-word sequence.

use crate::{parse_binary_source_words, BinarySourceWord};

const MAX_BYTES: usize = 4 * 1024 * 1024;
const MAX_WORDS: usize = 1_000_000;
const TAGGED_WIDTHS: [usize; 8] = [1, 3, 4, 5, 6, 7, 8, 9];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WordTagProbeError {
    EmptyProgram,
    TooLarge,
    Truncated,
    InvalidWidth,
    NoncanonicalTail,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct WordTagProbeAccounting {
    pub semantic_bits: usize,
    pub word_count: usize,
    pub d2_tag_bits: usize,
    pub non_d2_tag_bits: usize,
    pub count_prefix_bits: usize,
    pub encoded_bits: usize,
    pub tail_bits: usize,
    pub physical_bytes: usize,
}

fn emit_gamma(value: usize, output: &mut Vec<u8>) {
    let width = usize::BITS as usize - value.leading_zeros() as usize;
    for _ in 1..width { output.push(0); }
    for shift in (0..width).rev() {
        output.push(((value >> shift) & 1) as u8);
    }
}

fn gamma_bits(value: usize) -> usize {
    2 * (usize::BITS as usize - value.leading_zeros() as usize) - 1
}

fn pack(bits: &[u8]) -> Vec<u8> {
    let mut bytes = vec![0u8; bits.len().div_ceil(8)];
    for (i, bit) in bits.iter().enumerate() {
        if *bit != 0 { bytes[i / 8] |= 1 << (7 - i % 8); }
    }
    bytes
}

/// One gamma-coded positive number-of-words, followed by tagged exact words.
/// D2 is tagged with one bit, every other D1..D9 width with four bits.
pub fn encode_tagged_words(
    words: &[BinarySourceWord],
) -> Result<Vec<u8>, WordTagProbeError> {
    if words.is_empty() { return Err(WordTagProbeError::EmptyProgram); }
    if words.len() > MAX_WORDS { return Err(WordTagProbeError::TooLarge); }
    let bits_needed = gamma_bits(words.len()) +
        words.iter().map(|word| word.width() + if word.width() == 2 { 1 } else { 4 }).sum::<usize>();
    if bits_needed.div_ceil(8) > MAX_BYTES { return Err(WordTagProbeError::TooLarge); }

    let mut bits = Vec::with_capacity(bits_needed);
    emit_gamma(words.len(), &mut bits);
    for word in words {
        let width = word.width();
        if width == 2 {
            bits.push(0); // Only D2 has short width tag.
        } else {
            let Some(index) = TAGGED_WIDTHS.iter().position(|value| *value == width) else {
                return Err(WordTagProbeError::InvalidWidth);
            };
            bits.push(1);
            for shift in (0..3).rev() {
                bits.push(((index >> shift) & 1) as u8);
            }
        }
        for shift in (0..width).rev() {
            bits.push(((word.packed_bits() >> shift) & 1) as u8);
        }
    }
    Ok(pack(&bits))
}

struct BitCursor<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl BitCursor<'_> {
    fn bit(&mut self) -> Result<usize, WordTagProbeError> {
        if self.offset >= self.bytes.len() * 8 {
            return Err(WordTagProbeError::Truncated);
        }
        let bit = ((self.bytes[self.offset / 8] >> (7 - self.offset % 8)) & 1) as usize;
        self.offset += 1;
        Ok(bit)
    }
    fn fixed(&mut self, count: usize) -> Result<usize, WordTagProbeError> {
        let mut value = 0usize;
        for _ in 0..count {
            value = (value << 1) | self.bit()?;
        }
        Ok(value)
    }
    fn gamma(&mut self) -> Result<usize, WordTagProbeError> {
        let mut zeroes = 0usize;
        while self.bit()? == 0 {
            zeroes += 1;
            if zeroes >= usize::BITS as usize {
                return Err(WordTagProbeError::TooLarge);
            }
        }
        Ok((1usize << zeroes) | self.fixed(zeroes)?)
    }
}

/// Restore exact (width,bits) words, never guessing width or parsing bare
/// concatenation. Gamma word count terminates the program. Extra bytes,
/// noncanonical zero padding and unused trailing bits are rejected by replay.
pub fn decode_tagged_words(
    bytes: &[u8],
) -> Result<Vec<BinarySourceWord>, WordTagProbeError> {
    if bytes.is_empty() { return Err(WordTagProbeError::EmptyProgram); }
    if bytes.len() > MAX_BYTES { return Err(WordTagProbeError::TooLarge); }
    let mut cursor = BitCursor { bytes, offset: 0 };
    let n = cursor.gamma()?;
    if n == 0 { return Err(WordTagProbeError::EmptyProgram); }
    if n > MAX_WORDS || n > (bytes.len() * 8 / 3) {
        return Err(WordTagProbeError::TooLarge);
    }
    let mut rendered = Vec::with_capacity(n);
    for _ in 0..n {
        let width = if cursor.bit()? == 0 {
            2
        } else {
            TAGGED_WIDTHS[cursor.fixed(3)?]
        };
        let value = cursor.fixed(width)?;
        rendered.push(format!("{value:0width$b}"));
    }
    if bytes.len() * 8 - cursor.offset >= 8
        || (cursor.offset..bytes.len() * 8)
            .any(|i| bytes[i / 8] & (1 << (7 - i % 8)) != 0)
    {
        return Err(WordTagProbeError::NoncanonicalTail);
    }
    let tokens = parse_binary_source_words(&rendered.join(" "))
        .map_err(|_| WordTagProbeError::InvalidWidth)?;
    let exact: Vec<_> = tokens.into_iter().map(|token| token.word).collect();
    if encode_tagged_words(&exact)? != bytes {
        return Err(WordTagProbeError::NoncanonicalTail);
    }
    Ok(exact)
}

pub fn tagged_accounting(
    words: &[BinarySourceWord],
) -> Result<WordTagProbeAccounting, WordTagProbeError> {
    let physical_bytes = encode_tagged_words(words)?.len();
    let count_prefix_bits = gamma_bits(words.len());
    let semantic_bits = words.iter().map(|w| w.width()).sum::<usize>();
    let d2_tag_bits = words.iter().filter(|w| w.width() == 2).count();
    let non_d2_tag_bits = 4 * (words.len() - d2_tag_bits);
    let encoded_bits = count_prefix_bits + semantic_bits + d2_tag_bits + non_d2_tag_bits;
    Ok(WordTagProbeAccounting {
        semantic_bits, word_count: words.len(), d2_tag_bits, non_d2_tag_bits,
        count_prefix_bits, encoded_bits, tail_bits: physical_bytes * 8 - encoded_bits,
        physical_bytes,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{encode_ternary_words, encode_binary_delimited_words, parse_canonical_binary};
    use crate::syntax::ExprKind;

    fn words(source: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(source).unwrap().into_iter().map(|t| t.word).collect()
    }

    #[test]
    fn exact_user_demo_requires_one_more_final_close() {
        let unclosed = "10 111 10 001 10 01 01 10 001 10 01 01";
        assert!(parse_canonical_binary(unclosed).is_err());
        let corrected = format!("{unclosed} 01");
        let syntax = parse_canonical_binary(&corrected).unwrap();
        assert_eq!(syntax.len(), 1);
        let ExprKind::List(ref top) = syntax[0].kind else { panic!("expected outer D2 form"); };
        assert_eq!(top.len(), 3);
        for child in top.iter().skip(1) {
            assert!(matches!(child.kind, ExprKind::List(_)));
        }
        // This is a syntactic witness only, not a COND oracle-evaluation proof.
        let ws = words(&corrected);
        let packed = encode_tagged_words(&ws).unwrap();
        assert_eq!(decode_tagged_words(&packed).unwrap(), ws);
        let account = tagged_accounting(&ws).unwrap();
        assert_eq!(account.word_count, 13);
        assert_eq!(account.semantic_bits, 29);
        assert_eq!(account.d2_tag_bits, 10);
        assert_eq!(account.non_d2_tag_bits, 12);
        assert_eq!(account.count_prefix_bits, 7);
        assert_eq!(account.physical_bytes, 8);
    }

    #[test]
    fn d2_separator_between_forms_can_be_omitted_in_current_ast_grammar() {
        let with_sep = "10 101 00 10 110 01 01";
        let without_sep = "10 101 10 110 01 01";
        for source in [with_sep, without_sep] {
            let parsed = parse_canonical_binary(source).unwrap();
            assert_eq!(parsed.len(), 1);
            let ExprKind::List(ref outer) = parsed[0].kind else { panic!("D2 outer list"); };
            assert_eq!(outer.len(), 2);
            assert!(matches!(outer[1].kind, ExprKind::List(_)));
        }
        // The AST structure is equivalent; the typed-source-word sequence
        // deliberately differs. Removing D2(00) is normalization, not identity.
        let lhs = words(with_sep);
        let rhs = words(without_sep);
        assert_ne!(lhs, rhs);
        assert_eq!(decode_tagged_words(&encode_tagged_words(&lhs).unwrap()).unwrap(), lhs);
        assert_eq!(decode_tagged_words(&encode_tagged_words(&rhs).unwrap()).unwrap(), rhs);
    }

    #[test]
    fn exhaustive_d1_d9_word_identity_roundtrip() {
        for width in 1..=9usize {
            for value in 0..(1usize << width) {
                let source = format!("{value:0width$b}");
                let ws = words(&source);
                assert_eq!(decode_tagged_words(&encode_tagged_words(&ws).unwrap()).unwrap(), ws);
            }
        }
    }

    #[test]
    fn no_interword_delimiters_needed_and_old_collisions_are_separated() {
        let a = words("0 00");
        let b = words("000");
        assert_ne!(encode_tagged_words(&a).unwrap(), encode_tagged_words(&b).unwrap());
        assert_eq!(decode_tagged_words(&encode_tagged_words(&a).unwrap()).unwrap(), a);
        assert_eq!(decode_tagged_words(&encode_tagged_words(&b).unwrap()).unwrap(), b);
    }

    #[test]
    fn bounded_eos_and_zero_tail_reject_extra_bytes() {
        let input = words("10 111 10 001 10 01 01 10 001 10 01 01 01");
        let bytes = encode_tagged_words(&input).unwrap();
        let mut added = bytes.clone();
        added.push(0);
        assert_eq!(decode_tagged_words(&added), Err(WordTagProbeError::NoncanonicalTail));
        let mut changed = bytes.clone();
        *changed.last_mut().unwrap() |= 1;
        assert_eq!(decode_tagged_words(&changed), Err(WordTagProbeError::NoncanonicalTail));
        assert_eq!(encode_tagged_words(&[]), Err(WordTagProbeError::EmptyProgram));
    }

    #[test]
    fn bounded_sample_compare_actual_codec_sizes_not_theoretical_guess() {
        let ws = words("10 111 10 001 10 01 01 10 001 10 01 01 01");
        let tag_size = encode_tagged_words(&ws).unwrap().len();
        let t5_size = encode_ternary_words(&ws).unwrap().len();
        let bp_size = encode_binary_delimited_words(&ws).unwrap().len();
        assert_eq!((tag_size, t5_size), (8, 9));
        assert!(bp_size >= 1);
        // A larger study must use real approved program corpora.
    }
}
