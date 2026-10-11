//! TEST-ONLY RESEARCH: T5 without EOS=22 if and only if there is EXACTLY
//! one complete top-level D2 parenthesized form.
//!
//! The final *semantic* D2 CLOSE word 01 acts as the grammar terminator.
//! Missing physical trits at the end of the final T5 byte are padded with 2;
//! padding is explicitly bounded (0..4 trits) and tested by re-encoding.
//! This is not a new D2 semantic law, not a universal program codec,
//! and not merged into the owner-selected T5 production reader.
//!
//! Crucially: a naked atom, a stream of top-level forms, or a trailing
//! separator do NOT have the final-close EOF witness and MUST be rejected.

use crate::{parse_binary_source_words, parse_canonical_binary, BinarySourceWord};

const MAX_BYTES: usize = 4 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BracketEndError {
    EmptyProgram,
    NotOneParenthesizedForm,
    InvalidSourceWord,
    InvalidPhysicalByte,
    MalformedPadding,
    NoncanonicalBytes,
    TooLarge,
}

fn one_closed_root(words: &[BinarySourceWord]) -> Result<(), BracketEndError> {
    if words.is_empty() {
        return Err(BracketEndError::EmptyProgram);
    }
    let first_is_open = matches!(
        words.first(),
        Some(BinarySourceWord::W2(w)) if w.packed_bits() == 0b10
    );
    let last_is_close = matches!(
        words.last(),
        Some(BinarySourceWord::W2(w)) if w.packed_bits() == 0b01
    );
    if !first_is_open || !last_is_close {
        return Err(BracketEndError::NotOneParenthesizedForm);
    }
    let surface = words.iter().map(ToString::to_string)
        .collect::<Vec<_>>().join(" ");
    let ast = parse_canonical_binary(&surface)
        .map_err(|_| BracketEndError::NotOneParenthesizedForm)?;
    if ast.len() != 1 {
        return Err(BracketEndError::NotOneParenthesizedForm);
    }
    Ok(())
}

/// Encode only one complete D2 top-level form.
/// There is no EOS trit, no header, and no ASCII whitespace in bytes.
pub fn encode_bracket_end_t5(
    words: &[BinarySourceWord],
) -> Result<Vec<u8>, BracketEndError> {
    one_closed_root(words)?;
    let bit_count = words.iter().map(|w| w.width()).sum::<usize>();
    let trits = bit_count.checked_add(words.len() - 1)
        .ok_or(BracketEndError::TooLarge)?;
    let bytes = trits.div_ceil(5);
    if bytes > MAX_BYTES {
        return Err(BracketEndError::TooLarge);
    }
    let mut symbols = Vec::with_capacity(bytes * 5);
    for (i, word) in words.iter().enumerate() {
        if i > 0 {
            symbols.push(2);
        }
        for shift in (0..word.width()).rev() {
            symbols.push(((word.packed_bits() >> shift) & 1) as u8);
        }
    }
    debug_assert_eq!(symbols.len(), trits);
    symbols.resize(bytes * 5, 2); // physical padding, NOT another delimiter
    Ok(symbols.chunks_exact(5).map(|five| {
        five.iter().fold(0u16, |acc, d| acc * 3 + u16::from(*d)) as u8
    }).collect())
}

/// Decode only the constrained one-root subset. The *last D2 CLOSE*
/// proves structural completion. All remaining trits must be canonical
/// physical pad and there may never be five complete pad trits.
pub fn decode_bracket_end_t5(
    data: &[u8],
) -> Result<Vec<BinarySourceWord>, BracketEndError> {
    if data.is_empty() {
        return Err(BracketEndError::EmptyProgram);
    }
    if data.len() > MAX_BYTES {
        return Err(BracketEndError::TooLarge);
    }
    let mut trits = Vec::with_capacity(data.len() * 5);
    for byte in data {
        if *byte >= 243 {
            return Err(BracketEndError::InvalidPhysicalByte);
        }
        let mut n = *byte;
        let mut five = [0u8; 5];
        for digit in five.iter_mut().rev() {
            *digit = n % 3;
            n /= 3;
        }
        trits.extend_from_slice(&five);
    }
    let pad = trits.iter().rev().take_while(|d| **d == 2).count();
    if pad >= 5 {
        return Err(BracketEndError::MalformedPadding);
    }
    trits.truncate(trits.len() - pad);
    if trits.is_empty() || *trits.last().unwrap() == 2 {
        return Err(BracketEndError::NotOneParenthesizedForm);
    }
    let mut parts: Vec<String> = Vec::new();
    let mut current = String::new();
    for trit in trits {
        match trit {
            0 | 1 => {
                current.push(char::from(b'0' + trit));
                if current.len() > 9 {
                    return Err(BracketEndError::InvalidSourceWord);
                }
            }
            2 => {
                if current.is_empty() {
                    return Err(BracketEndError::InvalidSourceWord);
                }
                parts.push(std::mem::take(&mut current));
            }
            _ => unreachable!(),
        }
    }
    if current.is_empty() {
        return Err(BracketEndError::InvalidSourceWord);
    }
    parts.push(current);
    let parsed = parse_binary_source_words(&parts.join(" "))
        .map_err(|_| BracketEndError::InvalidSourceWord)?;
    let words = parsed.into_iter().map(|t| t.word).collect::<Vec<_>>();
    one_closed_root(&words)?;
    if encode_bracket_end_t5(&words)? != data {
        return Err(BracketEndError::NoncanonicalBytes);
    }
    Ok(words)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{encode_ternary_words, parse_canonical_binary};

    fn words(input: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(input).unwrap()
            .into_iter().map(|token| token.word).collect()
    }

    #[test]
    fn simple_root_close_replaces_22_and_saves_one_byte() {
        let source = "10 001 01";
        let ws = words(source);
        let no_eos = encode_bracket_end_t5(&ws).unwrap();
        let with_eos = encode_ternary_words(&ws).unwrap();
        assert_eq!(no_eos.len(), 2);
        assert_eq!(with_eos.len(), 3);
        assert_eq!(decode_bracket_end_t5(&no_eos).unwrap(), ws);
    }

    #[test]
    fn completely_empty_list_is_one_byte_without_22() {
        let ws = words("10 01");
        let physical = encode_bracket_end_t5(&ws).unwrap();
        assert_eq!(physical.len(), 1); // 2+1+2=5 trits, exact byte
        assert_eq!(decode_bracket_end_t5(&physical).unwrap(), ws);
        assert_eq!(encode_ternary_words(&ws).unwrap().len(), 2);
    }

    #[test]
    fn nested_brackets_finish_at_outermost_close_not_inner_close() {
        let input = words("10 001 10 000 01 01");
        let bytes = encode_bracket_end_t5(&input).unwrap();
        assert_eq!(decode_bracket_end_t5(&bytes).unwrap(), input);
        assert_eq!(parse_canonical_binary(
            &input.iter().map(ToString::to_string).collect::<Vec<_>>().join(" ")
        ).unwrap().len(), 1);
    }

    #[test]
    fn excludes_atoms_multiple_roots_and_trailing_separators() {
        for bad in ["000", "1", "10 001", "10 001 01 10 000 01",
                    "10 001 01 000", "10 001 01 00", "10 001 01 01"] {
            assert_eq!(encode_bracket_end_t5(&words(bad)),
                       Err(BracketEndError::NotOneParenthesizedForm), "{bad}");
        }
    }

    #[test]
    fn physical_padding_is_minimal_and_never_a_word_or_extra_eos() {
        let ws = words("10 001 01");
        let canonical = encode_bracket_end_t5(&ws).unwrap();
        let mut appended = canonical.clone();
        appended.push(242); // 22222 = five entire extra pad trits
        assert_eq!(decode_bracket_end_t5(&appended),
                   Err(BracketEndError::MalformedPadding));
        assert_eq!(decode_bracket_end_t5(&[243]),
                   Err(BracketEndError::InvalidPhysicalByte));
        let mut corrupted = canonical;
        *corrupted.last_mut().unwrap() -= 1; // mutate terminal physical pad 2
        assert!(decode_bracket_end_t5(&corrupted).is_err());
    }

    #[test]
    fn all_d1_to_d9_domain_word_values_survive_inside_a_root() {
        for width in 1usize..=9 {
            for value in 0..(1usize << width) {
                if width == 2 { // D2 payload is structural, not a generic value
                    continue;
                }
                let code = format!("{value:0width$b}");
                let ws = words(&format!("10 {code} 01"));
                let binary = encode_bracket_end_t5(&ws).unwrap();
                assert_eq!(decode_bracket_end_t5(&binary).unwrap(), ws);
            }
        }
    }

    #[test]
    fn compare_actual_t5_on_corrected_cond_demonstration() {
        let ws = words("10 111 10 001 10 01 01 10 001 10 01 01 01");
        let compact = encode_bracket_end_t5(&ws).unwrap();
        let legacy = encode_ternary_words(&ws).unwrap();
        assert_eq!(compact.len(), 9);
        assert_eq!(legacy.len(), 9);
        assert_eq!(decode_bracket_end_t5(&compact).unwrap(), ws);
    }
}
