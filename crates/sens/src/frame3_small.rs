//! Explicit-only, bounded reader for the original research F3 tiny format.
//!
//! T5 is normal .sens; F3 is separate .senc, only for very small programs
//! with full F3 carrier smaller than canonical T5. No sniffing or fallback.
//! The original mathematical Rust rank/unrank is imported, not reimplemented.
//! Restored words always pass the existing canonical SENS packed T5 reader.
#[allow(dead_code)]
#[path = "../../../research/framed3/rust_codec/senc.rs"]
mod original_f3;

use crate::{
    decode_ternary_words, encode_ternary_words, parse_binary_source_words, PhysicalT5Program,
};

pub const MAX_TINY_T5_BYTES: usize = 16;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SmallF3Error {
    WrongCarrier,
    InvalidFrame,
    InvalidProgram,
    NotSmallerThanT5,
}

/// Choose original F3 only for a canonical single-root tiny program if the
/// complete physical carrier (including 0xf3) saves bytes. Other canonical
/// T5 programs remain T5. This never mutates the input or falls back at decode.
pub fn encode_explicit_small_f3(t5_input: &[u8]) -> Result<Option<Vec<u8>>, SmallF3Error> {
    // Один точний T5 decode служить і перевірці форми, і canonical re-encode.
    // Повторний decode у цьому гарячому маршруті не додавав жодної перевірки.
    let typed = decode_ternary_words(t5_input).map_err(|_| SmallF3Error::InvalidProgram)?;
    let parsed =
        PhysicalT5Program::from_exact_words(&typed).map_err(|_| SmallF3Error::InvalidProgram)?;
    if parsed.form_count() != 1 || t5_input.len() > MAX_TINY_T5_BYTES {
        return Ok(None);
    }
    let current = encode_ternary_words(&typed).map_err(|_| SmallF3Error::InvalidProgram)?;
    if current != t5_input {
        return Err(SmallF3Error::InvalidProgram);
    }
    let exact = typed
        .iter()
        .map(|w| format!("{:0width$b}", w.packed_bits(), width = w.width()))
        .collect::<Vec<_>>();
    let body = match original_f3::frame_encode(&exact) {
        Ok(data) => data,
        Err(_) => return Ok(None),
    };
    let mut small = vec![original_f3::FRAME_LABEL];
    small.extend_from_slice(&body);
    if small.len() >= t5_input.len() {
        return Ok(None);
    }
    // Strict D3 code-admission, byte-exact canonical T5 word identity.
    match decode_explicit_small_f3(&small) {
        Ok(recovered) if recovered == t5_input => Ok(Some(small)),
        _ => Ok(None), // optional compression may be unsupported, T5 stays valid
    }
}

/// Decode explicitly provided .senc F3 bytes to the canonical physical T5
/// representation for the existing parser/executor. Callers MUST require the
/// .senc extension and an explicit F3 command, not byte autodetection.
pub fn decode_explicit_small_f3(input: &[u8]) -> Result<Vec<u8>, SmallF3Error> {
    // A 16B F3 file cannot be smaller than the permitted <=16B T5 input.
    if input.len() < 2
        || input.len() >= MAX_TINY_T5_BYTES
        || input.first() != Some(&original_f3::FRAME_LABEL)
    {
        return Err(SmallF3Error::WrongCarrier);
    }
    let words = original_f3::decode_senc(input).map_err(|_| SmallF3Error::InvalidFrame)?;
    let tokens =
        parse_binary_source_words(&words.join(" ")).map_err(|_| SmallF3Error::InvalidProgram)?;
    let typed = tokens.into_iter().map(|t| t.word).collect::<Vec<_>>();
    let t5 = encode_ternary_words(&typed).map_err(|_| SmallF3Error::InvalidProgram)?;

    if t5.len() > MAX_TINY_T5_BYTES || input.len() >= t5.len() {
        return Err(SmallF3Error::NotSmallerThanT5);
    }
    let parsed =
        PhysicalT5Program::from_exact_words(&typed).map_err(|_| SmallF3Error::InvalidProgram)?;
    if parsed.form_count() != 1 {
        return Err(SmallF3Error::InvalidProgram);
    }
    let validated = decode_ternary_words(&t5).map_err(|_| SmallF3Error::InvalidProgram)?;
    if validated != typed {
        return Err(SmallF3Error::InvalidProgram);
    }
    // Original F3 decode_senc already performs canonical physical re-encode.
    Ok(t5)
}

