//! Стерильний ABI v2 між SENS та будь-яким хостом для фізичних T5/F3C.
//! Owner law: Zig is the turnstile, not the registry; SENS decides meaning;
//! Rust holds opaque bytes. No local T5 algorithm lives in this module.
//! Zig зберігає ширину, порядок, біти й статус; жодного semantic admission.
//! Спільний Rust-викликач для `sens` і `sens-trit`, без дубльованого T5 reader.

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
    // SAFETY: the borrowed byte slice lives through the synchronous call.
    if unsafe { sens_zig_t5_validate(bytes.as_ptr(), bytes.len()) } != 0 {
        return Err("Zig physical T5 rejected; no SENS execution".into());
    }
    Ok(())
}

/// Zig is the physical encoder; SENS supplies exact qualified words.
/// The required T5 byte count follows solely from widths and separators.
pub fn encode_t5_direct(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() {
        return Err("Zig physical T5 cannot encode an empty record".into());
    }
    let be3_capacity = words
        .len()
        .checked_mul(3)
        .ok_or("Zig BE3 input length overflow")?;
    let mut be3 = Vec::with_capacity(be3_capacity);
    for word in words {
        let width = word.width();
        let bits = word.bits();
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

pub fn decode_t5_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
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
        let word = sens::BinarySourceWord::from_width_bits(width, bits)
            .map_err(|e| format!("Zig returned inadmissible coordinate: {e:?}"))?;
        words.push(word);
    }
    Ok(words)
}

pub fn encode_f3(t5: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    validate_t5(t5)?;
    let mut bytes = vec![0u8; t5.len().saturating_add(16).max(32)];
    let len = unsafe { sens_zig_f3c_pack(t5.as_ptr(), t5.len(), bytes.as_mut_ptr(), bytes.len()) };
    if len <= 0 {
        return Err(format!("explicit Zig F3C pack rejected: code={len}"));
    }
    bytes.truncate(len as usize);
    Ok(bytes)
}

pub fn decode_f3(bytes: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut t5 = vec![0u8; bytes.len().saturating_mul(4).max(32)];
    let len = unsafe {
        sens_zig_f3c_unpack(bytes.as_ptr(), bytes.len(), t5.as_mut_ptr(), t5.len())
    };
    if len <= 0 {
        return Err(format!("explicit Zig F3C rejected: code={len}"));
    }
    t5.truncate(len as usize);
    validate_t5(&t5)?;
    Ok(t5)
}
