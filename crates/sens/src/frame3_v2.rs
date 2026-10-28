//! Envelope E2: self-contained byte-DP over RAW/REPEAT/GRAMMAR.
//!
//! Historical wire/research name: S3/v2.  It is an Envelope, not Frame3/F3;
//! the old filename/API is retained only for compatibility with evidence/tests.
//!
//! S3 02 | minimal ULEB total-word-count |
//! [tag | minimal ULEB block-word-count | block data]* | CRC32.
//! Tags RAW=0 and REPEAT=1 retain v1 block payload rules.
//! GRAMMAR=2: minimal ULEB inner-bit-length (0..20) followed by the exact
//! fixed-width rank body of ONE complete D2 list, without its fixed 10/01.
//! The external byte count/word count, explicit inner length and final CRC
//! prevent EOF, rank and suffix ambiguity; encode(decode(bytes)) is canonical.
//! This is NOT a .sens default, a proof of the globally optimal compressor,
//! or a semantic validity oracle for executable D3 applications.

use super::{
    bits_to_bytes, bytes_to_words, get_varint, physical_crc32, put_varint, varint_len, Frame3Error,
    MAX_BLOCK_WORDS, MAX_FILE_BYTES, MAX_WORDS, RAW, REPEAT,
};
use crate::frame3_grammar::{
    count_inner, rank_binary_source_words, unrank_binary_source_words, GrammarRankError,
    MAX_INNER_BITS,
};
use crate::{parse_canonical_word_sequence, BinarySourceWord};

const MAGIC_V2: [u8; 3] = [b'S', b'3', 2];
const GRAMMAR: u8 = 2;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Choice {
    Raw,
    Repeat,
    Grammar,
}

#[derive(Clone, Copy, Debug)]
struct Step {
    bytes: usize,
    end: usize,
    mode: Choice,
}

fn grammar_error(error: GrammarRankError) -> Frame3Error {
    match error {
        GrammarRankError::TooLarge => Frame3Error::TooLarge,
        GrammarRankError::InvalidD2 => Frame3Error::InvalidD2,
        GrammarRankError::NonCanonical | GrammarRankError::OutOfRange => Frame3Error::NonCanonical,
        GrammarRankError::InvalidWord => Frame3Error::Malformed,
    }
}

fn grammar_body_bytes(bits: usize) -> Result<usize, Frame3Error> {
    let cap = count_inner(bits).map_err(grammar_error)?;
    let required_bits = (u128::BITS - (cap - 1).leading_zeros()) as usize;
    Ok(required_bits.div_ceil(8))
}

fn grammar_block(words: &[BinarySourceWord]) -> Option<(usize, u128)> {
    let first = words.first()?;
    let last = words.last()?;
    if words.len() < 2
        || first.width() != 2
        || first.packed_bits() != 0b10
        || last.width() != 2
        || last.packed_bits() != 0b01
    {
        return None;
    }
    let inner_bits = words[1..words.len() - 1]
        .iter()
        .map(|word| word.width())
        .sum::<usize>();
    if inner_bits > MAX_INNER_BITS {
        return None;
    }
    let rank = rank_binary_source_words(words).ok()?;
    debug_assert_eq!(usize::from(rank.inner_bits), inner_bits);
    Some((inner_bits, rank.ordinal))
}

fn plan_v2(words: &[BinarySourceWord]) -> Vec<Step> {
    let size = words.len();
    let mut steps = vec![
        Step {
            bytes: usize::MAX,
            end: size,
            mode: Choice::Raw,
        };
        size + 1
    ];
    steps[size].bytes = 0;
    for i in (0..size).rev() {
        let mut bits = 0usize;
        let mut same = true;
        for j in (i + 1)..=size.min(i + MAX_BLOCK_WORDS) {
            let word = words[j - 1];
            bits += word.width();
            same &= word == words[i];
            let count = j - i;
            let raw = 1 + varint_len(count) + count.div_ceil(2) + bits.div_ceil(8);
            let mut candidates = [(raw, Choice::Raw); 3];
            let mut n = 1;
            if same {
                let repeat = 1 + varint_len(count) + 1 + word.width().div_ceil(8);
                candidates[n] = (repeat, Choice::Repeat);
                n += 1;
            }
            if let Some((inner_bits, _)) = grammar_block(&words[i..j]) {
                if let Ok(body) = grammar_body_bytes(inner_bits) {
                    candidates[n] = (
                        1 + varint_len(count) + varint_len(inner_bits) + body,
                        Choice::Grammar,
                    );
                    n += 1;
                }
            }
            for (cost, mode) in candidates.into_iter().take(n) {
                let total = cost + steps[j].bytes;
                let current = steps[i];
                // Tie: prefer RAW, then REPEAT, then GRAMMAR; longer block last.
                let order = |mode| match mode {
                    Choice::Raw => 0u8,
                    Choice::Repeat => 1,
                    Choice::Grammar => 2,
                };
                if total < current.bytes
                    || (total == current.bytes
                        && (order(mode), usize::MAX - j)
                            < (order(current.mode), usize::MAX - current.end))
                {
                    steps[i] = Step {
                        bytes: total,
                        end: j,
                        mode,
                    };
                }
            }
        }
    }
    steps
}

// If no 128-word window can hold a complete, <=20-inner-bit D2 list,
// grammar cannot enter the admissible mode set. Reuse the ALREADY proven
// v1 RAW/REPEAT physical optimum instead of running another byte DP.
// This is a conservative necessary-condition filter, never grammar admission.
fn any_possible_grammar_block(words: &[BinarySourceWord]) -> bool {
    for start in 0..words.len() {
        let first = words[start];
        if first.width() != 2 || first.packed_bits() != 0b10 {
            continue;
        }
        let mut inner_bits = 0usize;
        for &word in words.iter().skip(start + 1).take(MAX_BLOCK_WORDS - 1) {
            if word.width() == 2 && word.packed_bits() == 0b01 && inner_bits <= MAX_INNER_BITS {
                return true;
            }
            inner_bits += word.width();
            if inner_bits > MAX_INNER_BITS {
                break;
            }
        }
    }
    false
}

/// Explicit v2 serializer. Does NOT replace \`universal_frame3::encode\` (v1).
pub fn encode_v2(words: &[BinarySourceWord]) -> Result<Vec<u8>, Frame3Error> {
    if words.len() > MAX_WORDS {
        return Err(Frame3Error::TooLarge);
    }
    parse_canonical_word_sequence(words).map_err(|_| Frame3Error::InvalidD2)?;
    if !any_possible_grammar_block(words) {
        // Same complete RAW/REPEAT cost function as v1. Only the explicit
        // version byte and its CRC change. No T5 migration or v1 behavior.
        let mut bytes = super::encode(words)?;
        bytes[2] = MAGIC_V2[2];
        let cutoff = bytes.len() - 4;
        let crc = physical_crc32(&bytes[..cutoff]).to_be_bytes();
        bytes[cutoff..].copy_from_slice(&crc);
        return Ok(bytes);
    }
    let plan = plan_v2(words);
    let mut result = Vec::with_capacity(3 + varint_len(words.len()) + plan[0].bytes + 4);
    result.extend_from_slice(&MAGIC_V2);
    put_varint(words.len(), &mut result);
    let mut at = 0usize;
    while at < words.len() {
        let step = plan[at];
        let chunk = &words[at..step.end];
        result.push(match step.mode {
            Choice::Raw => RAW,
            Choice::Repeat => REPEAT,
            Choice::Grammar => GRAMMAR,
        });
        put_varint(chunk.len(), &mut result);
        match step.mode {
            Choice::Raw => {
                for pair in chunk.chunks(2) {
                    let left = pair[0].width() as u8;
                    let right = pair.get(1).map_or(0, |word| word.width() as u8);
                    result.push((left << 4) | right);
                }
                result.extend_from_slice(&bits_to_bytes(chunk));
            }
            Choice::Repeat => {
                result.push(chunk[0].width() as u8);
                result.extend_from_slice(&bits_to_bytes(&chunk[..1]));
            }
            Choice::Grammar => {
                let (inner_bits, mut ordinal) =
                    grammar_block(chunk).ok_or(Frame3Error::InvalidD2)?;
                put_varint(inner_bits, &mut result);
                let nbytes = grammar_body_bytes(inner_bits)?;
                let mut payload = vec![0u8; nbytes];
                for byte in payload.iter_mut().rev() {
                    *byte = ordinal as u8;
                    ordinal >>= 8;
                }
                if ordinal != 0 {
                    return Err(Frame3Error::Malformed);
                }
                result.extend_from_slice(&payload);
            }
        }
        at = step.end;
    }
    let crc = physical_crc32(&result);
    result.extend_from_slice(&crc.to_be_bytes());
    if result.len() > MAX_FILE_BYTES {
        return Err(Frame3Error::TooLarge);
    }
    Ok(result)
}

/// Versioned physical reader, with fail-closed CRC, length, grammar and
/// canonical full-file re-encode checks. Old v1 bytes are NOT accepted.
pub fn decode_v2(bytes: &[u8]) -> Result<Vec<BinarySourceWord>, Frame3Error> {
    if bytes.len() > MAX_FILE_BYTES {
        return Err(Frame3Error::TooLarge);
    }
    if bytes.len() < MAGIC_V2.len() + 1 + 4 {
        return Err(Frame3Error::Truncated);
    }
    if bytes[..3] != MAGIC_V2 {
        return Err(Frame3Error::BadVersion);
    }
    let cutoff = bytes.len() - 4;
    let expected = u32::from_be_bytes(
        bytes[cutoff..]
            .try_into()
            .map_err(|_| Frame3Error::Truncated)?,
    );
    if physical_crc32(&bytes[..cutoff]) != expected {
        return Err(Frame3Error::Integrity);
    }
    let mut at = 3usize;
    let target = get_varint(&bytes[..cutoff], &mut at)?;
    if target > MAX_WORDS {
        return Err(Frame3Error::TooLarge);
    }
    let mut words = Vec::with_capacity(target);
    while words.len() < target {
        let mode = *bytes.get(at).ok_or(Frame3Error::Truncated)?;
        at += 1;
        let count = get_varint(&bytes[..cutoff], &mut at)?;
        if count == 0 || count > MAX_BLOCK_WORDS || count > target - words.len() {
            return Err(Frame3Error::Malformed);
        }
        match mode {
            RAW => {
                let map_len = count.div_ceil(2);
                let map_end = at.checked_add(map_len).ok_or(Frame3Error::Malformed)?;
                if map_end > cutoff {
                    return Err(Frame3Error::Truncated);
                }
                let mut widths = Vec::with_capacity(count);
                for &byte in &bytes[at..map_end] {
                    widths.push(usize::from(byte >> 4));
                    widths.push(usize::from(byte & 15));
                }
                if count % 2 != 0 && widths[count] != 0 {
                    return Err(Frame3Error::NonCanonical);
                }
                widths.truncate(count);
                if widths.iter().any(|width| !(1..=9).contains(width)) {
                    return Err(Frame3Error::Malformed);
                }
                at = map_end;
                let bit_len = widths.iter().sum::<usize>();
                let payload_end = at
                    .checked_add(bit_len.div_ceil(8))
                    .ok_or(Frame3Error::Malformed)?;
                if payload_end > cutoff {
                    return Err(Frame3Error::Truncated);
                }
                words.extend(bytes_to_words(&widths, &bytes[at..payload_end])?);
                at = payload_end;
            }
            REPEAT => {
                let width = usize::from(*bytes.get(at).ok_or(Frame3Error::Truncated)?);
                at += 1;
                if !(1..=9).contains(&width) {
                    return Err(Frame3Error::Malformed);
                }
                let end = at
                    .checked_add(width.div_ceil(8))
                    .ok_or(Frame3Error::Malformed)?;
                if end > cutoff {
                    return Err(Frame3Error::Truncated);
                }
                let one = bytes_to_words(&[width], &bytes[at..end])?[0];
                words.resize(words.len() + count, one);
                at = end;
            }
            GRAMMAR => {
                let inner_bits = get_varint(&bytes[..cutoff], &mut at)?;
                let payload_len = grammar_body_bytes(inner_bits)?;
                let end = at.checked_add(payload_len).ok_or(Frame3Error::Malformed)?;
                if end > cutoff {
                    return Err(Frame3Error::Truncated);
                }
                let mut ordinal = 0u128;
                for &byte in &bytes[at..end] {
                    ordinal = (ordinal << 8) | u128::from(byte);
                }
                let recovered =
                    unrank_binary_source_words(inner_bits, ordinal).map_err(grammar_error)?;
                if recovered.len() != count {
                    return Err(Frame3Error::NonCanonical);
                }
                words.extend(recovered);
                at = end;
            }
            _ => return Err(Frame3Error::Malformed),
        }
    }
    if at != cutoff {
        return Err(Frame3Error::NonCanonical);
    }
    parse_canonical_word_sequence(&words).map_err(|_| Frame3Error::InvalidD2)?;
    if encode_v2(&words)?.as_slice() != bytes {
        return Err(Frame3Error::NonCanonical);
    }
    Ok(words)
}

/// Byte-chunk accumulator; D2 validation happens at finish, not incrementally.
#[derive(Default)]
pub struct Frame3V2Decoder {
    bytes: Vec<u8>,
    poisoned: bool,
}

impl Frame3V2Decoder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn push(&mut self, chunk: &[u8]) -> Result<(), Frame3Error> {
        if self.poisoned {
            return Err(Frame3Error::TooLarge);
        }
        if chunk.len() > MAX_FILE_BYTES.saturating_sub(self.bytes.len()) {
            self.poisoned = true;
            return Err(Frame3Error::TooLarge);
        }
        self.bytes.extend_from_slice(chunk);
        Ok(())
    }

    pub fn finish(self) -> Result<Vec<BinarySourceWord>, Frame3Error> {
        if self.poisoned {
            return Err(Frame3Error::TooLarge);
        }
        decode_v2(&self.bytes)
    }
}

