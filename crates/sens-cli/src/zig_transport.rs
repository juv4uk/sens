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

/// Check only exact width/payload identity; never infer a callable SENS law.
/// A canonical physical frame may still carry DIFFERENT words after a codec
/// regression. The ABI result must retain the original domain coordinates.
fn require_same_exact_words(
    expected: &[sens::BinarySourceWord],
    actual: &[sens::BinarySourceWord],
) -> Result<(), String> {
    if expected.len() != actual.len() {
        return Err(format!(
            "ZIG_EGRESS_ROUNDTRIP_MISMATCH word_count expected={} actual={}",
            expected.len(), actual.len()
        ));
    }
    for (index, (left, right)) in expected.iter().zip(actual).enumerate() {
        if left.width() != right.width() || left.bits() != right.bits() {
            return Err(format!(
                "ZIG_EGRESS_ROUNDTRIP_MISMATCH index={index} expected_width={}                  expected_bits={:b} actual_width={} actual_bits={:b}",
                left.width(), left.bits(), right.width(), right.bits()
            ));
        }
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
        // The Rust enum is a carrier; preserve exact width without turning
        // it into a host function number or a historical SID8 identity.
        let width = u8::try_from(word.width())
            .map_err(|_| "Zig BE3 width does not fit in u8")?;
        let bits = word.packed_bits();
        if width == 0 || width > 9 {
            return Err(format!("unsupported physical T5 width {width}"));
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
    if len <= 0 || usize::try_from(len).ok().filter(|&n| n <= output.len()).is_none() {
        return Err(format!("Zig T5 encode rejected: code={len}"));
    }
    output.truncate(len as usize);
    validate_t5(&output)?;
    // Both directions use the sterile Zig ABI. No Rust T5 decoder or
    // semantic registry participates in the physical egress witness.
    let restored = decode_t5_words(&output)?;
    require_same_exact_words(words, &restored)?;
    Ok(output)
}

/// Механічна звірка зі збереженим еталоном. Фізичні байти створює лише Zig;
/// передані expected_bytes не використовуються як вихід або fallback.
pub fn encode_t5(
    words: &[sens::BinarySourceWord],
    expected_bytes: &[u8],
) -> Result<Vec<u8>, String> {
    let bytes = encode_t5_direct(words)?;
    if bytes != expected_bytes {
        return Err("Zig physical T5 differs from supplied reference bytes".into());
    }
    Ok(bytes)
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
    if len <= 0 || usize::try_from(len).ok().filter(|&n| n <= be3.len()).is_none() {
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
        // Restore only exact source word *shapes*. SENS alone admits D2 and
        // callable semantics later, Zig has provided physical width+payload.
        if width < 9 && bits > u16::from(u8::MAX) {
            return Err("Zig BE3 payload exceeds narrow carrier".into());
        }
        let low = bits as u8;
        let word = match width {
            1 => sens::Bit1::new(low).map(sens::BinarySourceWord::W1),
            2 => sens::Bit2::new(low).map(sens::BinarySourceWord::W2),
            3 => sens::Bit3::new(low).map(sens::BinarySourceWord::W3),
            4 => sens::Bit4::new(low).map(sens::BinarySourceWord::W4),
            5 => sens::Bit5::new(low).map(sens::BinarySourceWord::W5),
            6 => sens::Bit6::new(low).map(sens::BinarySourceWord::W6),
            7 => sens::Bit7::new(low).map(sens::BinarySourceWord::W7),
            8 => sens::Bit8::new(low).map(sens::BinarySourceWord::W8),
            9 => sens::Bit9::new(bits).map(sens::BinarySourceWord::W9),
            _ => None,
        }.ok_or_else(|| format!("Zig BE3 rejected exact carrier width={width}"))?;
        words.push(word);
    }
    Ok(words)
}

/// Фізичне F3C — виключно Zig. ABI -3 означає відсутність виграшу,
/// а НЕ невалідність звичайного T5. Немає автоматичного Rust fallback.
pub fn encode_f3(t5: &[u8]) -> Result<Option<Vec<u8>>, String> {
    version()?;
    validate_t5(t5)?;
    let mut bytes = vec![0u8; t5.len().saturating_add(16).max(32)];
    let len = unsafe { sens_zig_f3c_pack(t5.as_ptr(), t5.len(), bytes.as_mut_ptr(), bytes.len()) };
    if len == -3 {
        return Ok(None);
    }
    if len <= 0 || usize::try_from(len).ok().filter(|&n| n <= bytes.len()).is_none() {
        return Err(format!("explicit Zig F3C pack rejected: code={len}"));
    }
    bytes.truncate(len as usize);
    if bytes.len() >= t5.len() {
        return Err("Zig F3C returned a carrier without a physical saving".into());
    }
    Ok(Some(bytes))
}

pub fn decode_f3(bytes: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut t5 = vec![0u8; bytes.len().saturating_mul(4).max(32)];
    let len = unsafe {
        sens_zig_f3c_unpack(bytes.as_ptr(), bytes.len(), t5.as_mut_ptr(), t5.len())
    };
    if len <= 0 || usize::try_from(len).ok().filter(|&n| n <= t5.len()).is_none() {
        return Err(format!("explicit Zig F3C rejected: code={len}"));
    }
    t5.truncate(len as usize);
    validate_t5(&t5)?;
    Ok(t5)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zig_egress_exact_width_identity_rejects_mutations() {
        let expected = sens::parse_binary_source_words("1 01")
            .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
        let identical = expected.clone();
        require_same_exact_words(&expected, &identical).unwrap();

        // Same payload, different domain width: D1:1 is NOT D2:01.
        let wrong_width = sens::parse_binary_source_words("01 01")
            .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
        assert!(require_same_exact_words(&expected, &wrong_width)
            .unwrap_err().contains("index=0"));

        // One flipped binary bit must not survive roundtrip unnoticed.
        let flipped_bit = sens::parse_binary_source_words("0 01")
            .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
        assert!(require_same_exact_words(&expected, &flipped_bit)
            .unwrap_err().contains("index=0"));

        // Neither truncation nor extra words may give a false PASS.
        assert!(require_same_exact_words(&expected, &identical[..1])
            .unwrap_err().contains("word_count"));
    }

    #[test]
    fn zig_corridor_t5_parity_is_mechanical_not_a_semantic_oracle() {
        let source = "10 001 00 000 01";
        let words = sens::parse_binary_source_words(source)
            .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
        let golden = [0x63, 0x89, 0x06, 0xa1];
        assert_eq!(encode_t5_direct(&words).unwrap(), golden);
        assert_eq!(encode_t5(&words, &golden).unwrap(), golden);
        assert!(encode_t5(&words, &[0xa1]).is_err());
        assert_eq!(decode_t5_words(&golden).unwrap(), words);
    }

    #[test]
    fn zig_be3_keeps_d1_and_d2_distinct_with_one_bit_mutant() {
        // Equal payload, distinct exact width; neither is a semantic opcode.
        let one = sens::parse_binary_source_words("1").unwrap()[0].word;
        let two = sens::parse_binary_source_words("01").unwrap()[0].word;
        let a = encode_t5_direct(&[one]).unwrap();
        let b = encode_t5_direct(&[two]).unwrap();
        assert_eq!(a, [0xa1]);
        assert_eq!(b, [0x35]);
        assert_ne!(a, b);
        assert_eq!(decode_t5_words(&a).unwrap(), vec![one]);
        assert_eq!(decode_t5_words(&b).unwrap(), vec![two]);
        assert!(decode_t5_words(&[0xf3]).is_err());
    }

    #[test]
    fn zig_corridor_f3c_no_saving_is_not_a_rust_fallback() {
        let golden_t5 = [0x63, 0x89, 0x06, 0xa1];
        let packed = encode_f3(&golden_t5).unwrap().expect("F3C saves one physical byte");
        assert_eq!(packed, [0xf3, 0x40, 0x60]);
        assert_eq!(decode_f3(&packed).unwrap(), golden_t5);
        assert_eq!(encode_f3(&[0x64]).unwrap(), None);
        assert!(decode_f3(&[0xf3]).is_err());
    }
}
