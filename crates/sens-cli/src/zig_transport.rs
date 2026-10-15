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
    // E1 physical egress: BE3 exact words, no Rust repr or semantics.
    fn sens_zig_e1_encode_be3(
        input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_f3c_pack(
        input: *const u8, len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_f3c_unpack(
        input: *const u8, len: usize, output: *mut u8, capacity: usize
    ) -> isize;
}

// Zig writes only into caller-owned buffers: a positive F3C result can
// still report MORE bytes than capacity. Vec::truncate silently ignores it.
fn checked_f3c_output_len(len: isize, capacity: usize, operation: &str) -> Result<usize, String> {
    let written = usize::try_from(len)
        .map_err(|_| format!("Zig {operation} rejected: code={len}"))?;
    if written == 0 || written > capacity {
        return Err(format!(
            "Zig {operation} invalid ABI length: reported={len} capacity={capacity}"
        ));
    }
    Ok(written)
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
    let semantic_trits = words
        .iter()
        .try_fold(0usize, |n, word| n.checked_add(word.width()))
        .ok_or("Zig T5 semantic bit count overflow")?;
    let used_trits = semantic_trits
        .checked_add(words.len() - 1)
        .ok_or("Zig T5 separator count overflow")?;
    let physical_capacity = used_trits
        .checked_add(4)
        .ok_or("Zig T5 byte count overflow")?
        / 5;
    let mut be3 = Vec::with_capacity(be3_capacity);
    for word in words {
        let width = u8::try_from(word.width())
            .map_err(|_| "Zig T5 width out of one-byte ABI range")?;
        // BinarySourceWord is W1..W9 only; width>9 cannot appear from typed words.
        if width == 0 || width > 9 {
            return Err(format!("unsupported program-word width {width}"));
        }
        let bits = word.packed_bits();
        let limit = 1u32 << width;
        if (bits as u32) >= limit {
            return Err(format!("payload overflow for width {width}"));
        }
        be3.push(width);
        be3.push((bits >> 8) as u8);
        be3.push(bits as u8);
    }
    let mut bytes = vec![0u8; physical_capacity];
    // SAFETY: Zig ABI v2 reads and writes only caller-owned byte slices.
    let len = unsafe {
        sens_zig_t5_encode_be3(be3.as_ptr(), be3.len(), bytes.as_mut_ptr(), bytes.len())
    };
    if len < 0 || usize::try_from(len).ok() != Some(bytes.len()) {
        return Err(format!("Zig physical T5 encode rejected: code={len}"));
    }
    Ok(bytes)
}

/// Optional mechanical comparison to the existing Rust reference bytes.
/// The reference never controls the actual produced T5 output buffer.
pub fn encode_t5(
    words: &[sens::BinarySourceWord],
    expected_bytes: &[u8],
) -> Result<Vec<u8>, String> {
    let bytes = encode_t5_direct(words)?;
    if bytes != expected_bytes {
        return Err("Zig T5 and admitted SENS reference differ at a physical byte".into());
    }
    Ok(bytes)
}

/// Zig is the only physical T5 decoder on the feature-gated eval ingress.
/// ABI v2 carries only [width, MSB, LSB] bytes, never Rust enum layout.
/// Exact words are subsequently admitted by SENS's existing D2 reader.
/// Width 10 is a mechanical coordinate only; program ingress stays W1..W9.
pub fn decode_t5_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
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
    // SAFETY: caller-owned slices outlive this synchronous Zig v2 ABI.
    let written = unsafe {
        sens_zig_t5_decode_be3(bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len())
    };
    if written <= 0
        || usize::try_from(written)
            .ok()
            .filter(|&n| n <= be3.len())
            .is_none()
        || written % 3 != 0
    {
        return Err(format!("Zig physical T5 decode rejected: code={written}"));
    }
    be3.truncate(written as usize);
    let mut words = Vec::with_capacity(be3.len() / 3);
    for triple in be3.chunks_exact(3) {
        let width = triple[0];
        let payload = (u16::from(triple[1]) << 8) | u16::from(triple[2]);
        // Host integer is only the bounded carrier of exact bits.
        if width < 9 && payload > u16::from(u8::MAX) {
            return Err("Zig BE3 payload exceeds declared narrow width".into());
        }
        let low = payload as u8;
        let word = match width {
            1 => sens::Bit1::new(low).map(sens::BinarySourceWord::W1),
            2 => sens::Bit2::new(low).map(sens::BinarySourceWord::W2),
            3 => sens::Bit3::new(low).map(sens::BinarySourceWord::W3),
            4 => sens::Bit4::new(low).map(sens::BinarySourceWord::W4),
            5 => sens::Bit5::new(low).map(sens::BinarySourceWord::W5),
            6 => sens::Bit6::new(low).map(sens::BinarySourceWord::W6),
            7 => sens::Bit7::new(low).map(sens::BinarySourceWord::W7),
            8 => sens::Bit8::new(low).map(sens::BinarySourceWord::W8),
            9 => sens::Bit9::new(payload).map(sens::BinarySourceWord::W9),
            // D10 is representable on the ladder, not a program BinarySourceWord.
            10 => {
                return Err(
                    "Zig BE3 width=10 is a mechanical coordinate, not program ingress".into(),
                )
            }
            _ => None,
        }
        .ok_or_else(|| format!("Zig BE3 invalid exact word width={width}"))?;
        words.push(word);
    }
    Ok(words)
}

/// E1 physical byte writer is exclusively Zig; Rust conveys only exact
/// W1..W9 BE3 triplets admitted by the canonical SENS word reader.
pub fn encode_e1_direct(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() || words.len() > 4096 {
        return Err("Zig E1 requires 1..4096 exact width/payload words".into());
    }
    let be3_capacity = words.len().checked_mul(3)
        .ok_or("Zig E1 BE3 input capacity overflow")?;
    let mut be3 = Vec::with_capacity(be3_capacity);
    for word in words {
        let width = u8::try_from(word.width())
            .map_err(|_| "Zig E1 width exceeds BE3 field")?;
        let bits = word.packed_bits();
        if width == 0 || width > 9 || (bits as u32) >= (1u32 << width) {
            return Err(format!("Zig E1 invalid exact-width payload width={width}"));
        }
        be3.extend_from_slice(&[width, (bits >> 8) as u8, bits as u8]);
    }
    // Conservative upper bound: a one-word RAW block fits 16 bytes per
    // word; Zig determines the actual canonical E1 byte count.
    let capacity = words.len().checked_mul(16)
        .and_then(|n| n.checked_add(16))
        .ok_or("Zig E1 output capacity overflow")?;
    let mut output = vec![0u8; capacity];
    // SAFETY: caller-owned disjoint buffers; Zig validates source and bounds.
    let written = unsafe {
        sens_zig_e1_encode_be3(
            be3.as_ptr(), be3.len(), output.as_mut_ptr(), output.len()
        )
    };
    if written <= 0 || usize::try_from(written).ok().filter(|&n| n <= output.len()).is_none() {
        return Err(format!("Zig E1 physical encode rejected: code={written}"));
    }
    output.truncate(written as usize);
    Ok(output)
}

/// Фізичне F3C — виключно Zig. ABI -3 означає відсутність виграшу,
/// а НЕ невалідність звичайного T5. Немає автоматичного Rust fallback.
pub fn encode_f3(t5: &[u8]) -> Result<Option<Vec<u8>>, String> {
    version()?;
    if t5.len() > 16 {
        return Ok(None);
    }
    validate_t5(t5)?;
    let mut bytes = vec![0u8; 16];
    // SAFETY: Zig writes at most the provided capacity.
    let len = unsafe { sens_zig_f3c_pack(t5.as_ptr(), t5.len(), bytes.as_mut_ptr(), bytes.len()) };
    if len == -3 {
        return Ok(None); // not smaller: T5 remains production
    }
    let written = checked_f3c_output_len(len, bytes.len(), "F3C pack")?;
    if written >= t5.len() {
        return Err("Zig F3C did not save bytes".into());
    }
    bytes.truncate(written);
    Ok(Some(bytes))
}

pub fn decode_f3(carrier: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut output = vec![0u8; 16];
    // SAFETY: caller owns valid input/output slices until call returns.
    let len = unsafe {
        sens_zig_f3c_unpack(
            carrier.as_ptr(),
            carrier.len(),
            output.as_mut_ptr(),
            output.len(),
        )
    };
    let written = checked_f3c_output_len(len, output.len(), "F3C unpack")?;
    output.truncate(written);
    // Zig first, then the existing SENS canonical parser/evaluator.
    validate_t5(&output)?;
    Ok(output)
}

#[cfg(test)]
mod f3c_abi_length_tests {
    use super::checked_f3c_output_len;

    #[test]
    fn f3c_caller_owned_output_length_accepts_only_written_bytes() {
        assert_eq!(checked_f3c_output_len(3, 16, "F3C pack").unwrap(), 3);
        assert_eq!(checked_f3c_output_len(16, 16, "F3C unpack").unwrap(), 16);
    }

    #[test]
    fn f3c_rejects_negative_zero_and_overreported_lengths() {
        for (reported, capacity) in [(-3, 16), (-2, 16), (-1, 16), (0, 16), (17, 16)] {
            assert!(
                checked_f3c_output_len(reported, capacity, "F3C unpack").is_err(),
                "invalid Zig ABI return {reported} must fail closed"
            );
        }
        assert!(checked_f3c_output_len(isize::MAX, 16, "F3C pack").is_err());
    }
}
