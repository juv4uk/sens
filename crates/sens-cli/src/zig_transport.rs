//! Стерильний ABI v2 між SENS та будь-яким хостом для фізичних T5/F3C/E1.
//! Owner law: Zig is the turnstile, not the registry; SENS decides meaning;
//! Rust holds opaque bytes. No local T5/E1 algorithm lives in this module.

unsafe extern "C" {
    fn sens_zig_codec_abi_version() -> u32;
    fn sens_zig_t5_validate(input: *const u8, len: usize) -> i32;
    fn sens_zig_t5_encode_be3(
        input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_t5_decode_be3(
        input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_e1_encode_be3(
        input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_e1_decode_be3(
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
    if unsafe { sens_zig_codec_abi_version() } != 2 {
        return Err("Zig codec C ABI version mismatch".into());
    }
    Ok(())
}

/// Механічний інваріант SENS ↔ Zig: кількість, ширина, біти.
/// Не визначає значення функцій і не замінює SENS-семантичний оракул.
fn require_same_exact_words(
    expected: &[sens::BinarySourceWord],
    actual: &[sens::BinarySourceWord],
) -> Result<(), String> {
    if expected.len() != actual.len() {
        return Err(format!(
            "ZIG_EGRESS_ROUNDTRIP_MISMATCH word_count expected={} actual={}",
            expected.len(),
            actual.len()
        ));
    }
    for (index, (left, right)) in expected.iter().zip(actual).enumerate() {
        if left.width() != right.width() || left.packed_bits() != right.packed_bits() {
            return Err(format!(
                "ZIG_EGRESS_ROUNDTRIP_MISMATCH index={index} expected_width={} expected_bits={:b} actual_width={} actual_bits={:b}",
                left.width(), left.packed_bits(), right.width(), right.packed_bits()
            ));
        }
    }
    Ok(())
}

pub fn validate_t5(bytes: &[u8]) -> Result<(), String> {
    version()?;
    if unsafe { sens_zig_t5_validate(bytes.as_ptr(), bytes.len()) } != 0 {
        return Err("Zig physical T5 rejected; no SENS execution".into());
    }
    Ok(())
}

pub fn encode_t5_direct(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() {
        return Err("Zig physical T5 cannot encode an empty record".into());
    }
    let be3_capacity = words.len().checked_mul(3).ok_or("Zig BE3 input length overflow")?;
    let semantic_trits = words
        .iter()
        .try_fold(0usize, |n, word| n.checked_add(word.width()))
        .ok_or("Zig T5 semantic bit count overflow")?;
    let used_trits = semantic_trits
        .checked_add(words.len() - 1)
        .ok_or("Zig T5 separator count overflow")?;
    let physical_capacity = used_trits.checked_add(4).ok_or("Zig T5 byte count overflow")? / 5;
    let mut be3 = Vec::with_capacity(be3_capacity);
    for word in words {
        let width = u8::try_from(word.width()).map_err(|_| "Zig T5 width out of one-byte ABI range")?;
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
    let len = unsafe {
        sens_zig_t5_encode_be3(be3.as_ptr(), be3.len(), bytes.as_mut_ptr(), bytes.len())
    };
    if len < 0 || usize::try_from(len).ok() != Some(bytes.len()) {
        return Err(format!("Zig physical T5 encode rejected: code={len}"));
    }
    // Обидва напрями проходять тільки стерильний Zig ABI, без Rust T5 codec.
    let restored = decode_t5_words(&bytes)?;
    require_same_exact_words(words, &restored)?;
    Ok(bytes)
}

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

pub fn decode_t5_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    validate_t5(bytes)?;
    let trits = bytes.len().checked_mul(5).ok_or("T5 input length overflow")?;
    let max_words = trits.checked_add(1).ok_or("T5 word count overflow")? / 2;
    let capacity = max_words.checked_mul(3).ok_or("T5 BE3 capacity overflow")?;
    let mut be3 = vec![0u8; capacity];
    let written = unsafe {
        sens_zig_t5_decode_be3(bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len())
    };
    if written <= 0
        || usize::try_from(written).ok().filter(|&n| n <= be3.len()).is_none()
        || written % 3 != 0
    {
        return Err(format!("Zig physical T5 decode rejected: code={written}"));
    }
    be3.truncate(written as usize);
    let mut words = Vec::with_capacity(be3.len() / 3);
    for triple in be3.chunks_exact(3) {
        let width = triple[0];
        let payload = (u16::from(triple[1]) << 8) | u16::from(triple[2]);
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
            10 => {
                return Err("Zig BE3 width=10 is a mechanical coordinate, not program ingress".into())
            }
            _ => None,
        }
        .ok_or_else(|| format!("Zig BE3 invalid exact word width={width}"))?;
        words.push(word);
    }
    Ok(words)
}

pub fn encode_e1_direct(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() {
        return Err("Zig E1 cannot encode an empty record".into());
    }
    let mut be3 = Vec::with_capacity(words.len().saturating_mul(3));
    for word in words {
        let width = u8::try_from(word.width()).map_err(|_| "Zig E1 width out of one-byte ABI range")?;
        if width == 0 || width > 9 {
            return Err(format!("Zig E1 invalid exact-width payload width={width}"));
        }
        let bits = word.packed_bits();
        if (bits as u32) >= (1u32 << width) {
            return Err(format!("Zig E1 payload overflow width={width}"));
        }
        be3.extend_from_slice(&[width, (bits >> 8) as u8, bits as u8]);
    }
    let capacity = words
        .len()
        .checked_mul(16)
        .and_then(|n| n.checked_add(16))
        .ok_or("Zig E1 output capacity overflow")?;
    let mut output = vec![0u8; capacity];
    let written = unsafe {
        sens_zig_e1_encode_be3(be3.as_ptr(), be3.len(), output.as_mut_ptr(), output.len())
    };
    if written <= 0 || usize::try_from(written).ok().filter(|&n| n <= output.len()).is_none() {
        return Err(format!("Zig E1 physical encode rejected: code={written}"));
    }
    output.truncate(written as usize);
    Ok(output)
}

/// Zig is the only physical E1 decoder on the feature-gated CLI ingress.
pub fn decode_e1_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    version()?;
    // The current Zig E1 ABI has a bounded 64 KiB canonical replay window.
    // E1 REPEAT can encode up to 4096 exact words in a very short frame;
    // allocating from input byte length loses valid repeated-word programs.
    if bytes.is_empty() || bytes.len() > 64 * 1024 {
        return Err("Zig E1 physical frame outside bounded decode window".into());
    }
    const MAX_E1_WORDS: usize = 4096;
    let mut be3 = vec![0u8; MAX_E1_WORDS * 3];
    let written = unsafe {
        sens_zig_e1_decode_be3(bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len())
    };
    if written <= 0
        || usize::try_from(written)
            .ok()
            .filter(|&n| n <= be3.len() && n % 3 == 0)
            .is_none()
    {
        return Err(format!("Zig E1 physical decode rejected: code={written}"));
    }
    be3.truncate(written as usize);
    let mut words = Vec::with_capacity(be3.len() / 3);
    for triple in be3.chunks_exact(3) {
        let width = triple[0];
        let payload = (u16::from(triple[1]) << 8) | u16::from(triple[2]);
        if width < 9 && payload > u16::from(u8::MAX) {
            return Err("Zig E1 BE3 payload exceeds declared narrow width".into());
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
            _ => None,
        }
        .ok_or_else(|| format!("Zig E1 BE3 invalid exact word width={width}"))?;
        words.push(word);
    }
    Ok(words)
}

pub fn encode_f3(t5: &[u8]) -> Result<Option<Vec<u8>>, String> {
    version()?;
    if t5.len() > 16 {
        return Ok(None);
    }
    validate_t5(t5)?;
    let mut bytes = vec![0u8; 16];
    let len = unsafe { sens_zig_f3c_pack(t5.as_ptr(), t5.len(), bytes.as_mut_ptr(), bytes.len()) };
    if len == -3 {
        return Ok(None);
    }
    if len <= 0 {
        return Err(format!("Zig F3C pack rejected: code={len}"));
    }
    bytes.truncate(len as usize);
    if bytes.len() >= t5.len() {
        return Err("Zig F3C did not save bytes".into());
    }
    Ok(Some(bytes))
}

pub fn decode_f3(carrier: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut output = vec![0u8; 16];
    let len = unsafe {
        sens_zig_f3c_unpack(carrier.as_ptr(), carrier.len(), output.as_mut_ptr(), output.len())
    };
    if len <= 0 {
        return Err(format!("explicit Zig F3C rejected: code={len}"));
    }
    output.truncate(len as usize);
    validate_t5(&output)?;
    Ok(output)
}

#[cfg(test)]
mod zig_exact_egress_tests {
    use super::{decode_t5_words, encode_t5_direct, require_same_exact_words};

    fn words(source: &str) -> Vec<sens::BinarySourceWord> {
        sens::parse_binary_source_words(source)
            .expect("точні двійкові слова")
            .into_iter()
            .map(|token| token.word)
            .collect()
    }

    #[test]
    fn t5_egress_uses_zig_for_exact_roundtrip() {
        let expected = words("1 01 001 010101000");
        let physical = encode_t5_direct(&expected).expect("Zig T5 encode");
        let recovered = decode_t5_words(&physical).expect("Zig T5 decode");
        require_same_exact_words(&expected, &recovered).unwrap();
        assert_eq!(physical.len(), 4);
    }

    #[test]
    fn t5_egress_blocks_width_bit_and_count_drift() {
        let expected = words("1 01");
        let changed_width = require_same_exact_words(&expected, &words("01 01"))
            .expect_err("D1:1 і D2:01 — різні слова");
        assert!(changed_width.contains("index=0"));
        assert!(changed_width.contains("expected_width=1"));
        assert!(changed_width.contains("actual_width=2"));
        assert!(require_same_exact_words(&expected, &words("0 01"))
            .unwrap_err().contains("index=0"));
        assert!(require_same_exact_words(&expected, &words("1"))
            .unwrap_err().contains("word_count expected=2 actual=1"));
        assert!(require_same_exact_words(&expected, &words("1 01 0"))
            .unwrap_err().contains("word_count expected=2 actual=3"));
    }
}
