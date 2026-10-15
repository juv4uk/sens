//! Sterile Zig physical corridor: Rust \u2194 SENS wire bytes.
//!
//! Owner law 2026-10-14: Zig is the turnstile, never the semantic registry.
//! Rust may hold opaque bytes or pass typed width/payload triplets; SENS alone
//! decides meaning. This module contains **no** local T5/F3C codec algorithm \u2014
//! only FFI to `research/zig-codecs/transport_abi.zig` (ABI v2).
//!
//! Production CLI default is `zig-transport`. A Rust-only build is an explicit
//! `--no-default-features` comparison mode, never a silent fallback.

unsafe extern "C" {
    fn sens_zig_codec_abi_version() -> u32;
    fn sens_zig_t5_validate(input: *const u8, len: usize) -> i32;
    // ABI v2: caller-owned width + big-endian payload triplets.
    // Never send repr(C)/repr(Rust) structs across the language boundary.
    fn sens_zig_t5_encode_be3(
        input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_t5_decode_be3(
        input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_f3c_pack(
        input: *const u8, len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_f3c_unpack(
        input: *const u8, len: usize, output: *mut u8, capacity: usize
    ) -> isize;
}

fn version() -> Result<(), String> {
    // SAFETY: zero-argument pure function from a statically linked Zig library.
    if unsafe { sens_zig_codec_abi_version() } != 2 {
        return Err("Zig codec C ABI version mismatch".into());
    }
    Ok(())
}

pub fn validate_t5(bytes: &[u8]) -> Result<(), String> {
    version()?;
    // SAFETY: input is a valid Rust slice; Zig only reads these bytes.
    let code = unsafe { sens_zig_t5_validate(bytes.as_ptr(), bytes.len()) };
    if code != 0 {
        return Err(format!("Zig T5 rejected physical program: code={code}"));
    }
    Ok(())
}

/// Encode typed exact-width words as BE3 triplets through Zig, then pack T5.
/// `words` are (width, payload) with width as identity \u2014 not host bools.
pub fn encode_t5_direct(words: &[(u8, u16)]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() {
        return Err("empty exact-domain word stream".into());
    }
    let mut be3 = Vec::with_capacity(words.len().saturating_mul(3));
    for &(width, bits) in words {
        if width == 0 || width > 10 {
            return Err(format!("unsupported domain width {width}"));
        }
        let limit = 1u32 << width;
        if (bits as u32) >= limit {
            return Err(format!("payload overflow for width {width}"));
        }
        be3.push(width);
        be3.push((bits >> 8) as u8);
        be3.push((bits & 0xff) as u8);
    }
    let capacity = be3.len().saturating_mul(2).max(16);
    let mut output = vec![0u8; capacity];
    // SAFETY: disjoint buffers; Zig does not free caller memory.
    let len = unsafe {
        sens_zig_t5_encode_be3(be3.as_ptr(), be3.len(), output.as_mut_ptr(), output.len())
    };
    if len <= 0 {
        return Err(format!("Zig T5 encode rejected: code={len}"));
    }
    output.truncate(len as usize);
    validate_t5(&output)?;
    Ok(output)
}

pub fn decode_t5_words(bytes: &[u8]) -> Result<Vec<(u8, u16)>, String> {
    version()?;
    validate_t5(bytes)?;
    let trits = bytes
        .len()
        .checked_mul(5)
        .ok_or("T5 input length overflow")?;
    let max_words = trits.checked_add(1).ok_or("T5 word count overflow")? / 2;
    let capacity = max_words
        .checked_mul(3)
        .ok_or("T5 BE3 capacity overflow")?;
    let mut be3 = vec![0u8; capacity];
    // SAFETY: input/output are valid non-overlapping slices for Zig decode.
    let len = unsafe {
        sens_zig_t5_decode_be3(bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len())
    };
    if len <= 0 {
        return Err(format!("Zig T5 decode rejected: code={len}"));
    }
    if (len as usize) % 3 != 0 {
        return Err("Zig T5 decode returned non-triplet length".into());
    }
    be3.truncate(len as usize);
    let mut words = Vec::with_capacity(be3.len() / 3);
    for chunk in be3.chunks_exact(3) {
        let width = chunk[0];
        let bits = u16::from_be_bytes([chunk[1], chunk[2]]);
        if width == 0 || width > 10 {
            return Err(format!("Zig returned invalid width {width}"));
        }
        let limit = 1u32 << width;
        if (bits as u32) >= limit {
            return Err(format!("Zig returned payload overflow width={width}"));
        }
        words.push((width, bits));
    }
    Ok(words)
}

pub fn encode_f3(t5_bytes: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    validate_t5(t5_bytes)?;
    let mut output = vec![0u8; t5_bytes.len().saturating_add(16).max(32)];
    let len = unsafe {
        sens_zig_f3c_pack(
            t5_bytes.as_ptr(),
            t5_bytes.len(),
            output.as_mut_ptr(),
            output.len(),
        )
    };
    if len <= 0 {
        return Err(format!("explicit Zig F3C pack rejected: code={len}"));
    }
    output.truncate(len as usize);
    Ok(output)
}

pub fn decode_f3(bytes: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut output = vec![0u8; bytes.len().saturating_mul(4).max(32)];
    let len = unsafe {
        sens_zig_f3c_unpack(bytes.as_ptr(), bytes.len(), output.as_mut_ptr(), output.len())
    };
    if len <= 0 {
        return Err(format!("explicit Zig F3C rejected: code={len}"));
    }
    output.truncate(len as usize);
    // Zig first, then the existing SENS canonical parser/evaluator.
    validate_t5(&output)?;
    Ok(output)
}
