//! Стерильний ABI v2 між SENS та будь-яким хостом для фізичних T5/F3C/E1.
//! Owner law: Zig is the turnstile, not the registry; SENS decides meaning;
//! Rust holds opaque bytes. No local T5/E1 algorithm lives in this module.

// Root-Zig opaque asset copies are a separate adapter, NOT codec ABI v2.
#[path = "zig_transport_assets.rs"]
mod asset_ffi;

unsafe extern "C" {
    fn sens_zig_codec_abi_version() -> u32;
    fn sens_zig_t5_validate(input: *const u8, len: usize) -> i32;
    // Coordinate-only D1..D10 physical validation; no runnable D10 admission.
    fn sens_zig_t5_validate_coordinates(input: *const u8, len: usize) -> i32;
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
/// Retrieves opaque source bytes through the sterile Zig C ABI.
/// No direct Rust include/open of lib/linter.lisp and no semantic work in Zig.
pub fn linter_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_linter_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_LINTER_CARRIER invalid source length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_LINTER_CARRIER length overflow")?;
    // Host memory bound. This is not a SENS domain/semantic admission threshold.
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_LINTER_CARRIER source exceeds host byte limit".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_linter_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_LINTER_CARRIER byte copy rejected: code={copied}"));
    }
    Ok(bytes)
}

/// Exact opaque project contract via Zig ABI. Zig does not interpret it.
pub fn contract_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_contract_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 { return Err("ZIG_CONTRACT_CARRIER invalid length".into()); }
    let len = usize::try_from(required).map_err(|_| "ZIG_CONTRACT_CARRIER overflow")?;
    if len > 8 * 1024 * 1024 { return Err("ZIG_CONTRACT_CARRIER host byte cap".into()); }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_contract_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required { return Err(format!("ZIG_CONTRACT_CARRIER mismatch: {copied}")); }
    Ok(bytes)
}

/// Opaque Sanskrit REPL source from the root Zig module, without Rust file access.
pub fn sanskrit_surface_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_sanskrit_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 { return Err("ZIG_SANSKRIT_CARRIER invalid length".into()); }
    let len = usize::try_from(required).map_err(|_| "ZIG_SANSKRIT_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 { return Err("ZIG_SANSKRIT_CARRIER host byte limit".into()); }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_sanskrit_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required { return Err(format!("ZIG_SANSKRIT_CARRIER copy mismatch: {copied}")); }
    Ok(bytes)
}

/// Opaque full-Ukrainian REPL source; Zig is only a byte corridor.
pub fn ukr_surface_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_ukr_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 { return Err("ZIG_UKR_CARRIER invalid length".into()); }
    let len = usize::try_from(required).map_err(|_| "ZIG_UKR_CARRIER overflow")?;
    if len > 8 * 1024 * 1024 { return Err("ZIG_UKR_CARRIER host limit".into()); }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_ukr_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required { return Err(format!("ZIG_UKR_CARRIER copy mismatch: {copied}")); }
    Ok(bytes)
}

/// Compact Ukrainian source goes through sterile Zig byte transport only.
pub fn uk_surface_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_uk_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 { return Err("ZIG_UK_CARRIER invalid length".into()); }
    let len = usize::try_from(required).map_err(|_| "ZIG_UK_CARRIER size overflow")?;
    if len > 8 * 1024 * 1024 { return Err("ZIG_UK_CARRIER host bound".into()); }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_uk_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required { return Err(format!("ZIG_UK_CARRIER mismatch: {copied}")); }
    Ok(bytes)
}

/// Release distribution JSON is copied as opaque bytes from root Zig 0.16.
/// Rust may validate the manifest protocol but cannot embed project sources.
pub fn islands_manifest_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_islands_manifest_bytes_copy(
            std::ptr::NonNull::<u8>::dangling().as_ptr(), 0
        )
    };
    if required <= 0 {
        return Err("ZIG_ISLANDS_MANIFEST_CARRIER invalid exact byte length".into());
    }
    let len = usize::try_from(required)
        .map_err(|_| "ZIG_ISLANDS_MANIFEST_CARRIER byte length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_ISLANDS_MANIFEST_CARRIER host byte cap exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe {
        asset_ffi::sens_zig_islands_manifest_bytes_copy(bytes.as_mut_ptr(), bytes.len())
    };
    if copied != required {
        return Err(format!("ZIG_ISLANDS_MANIFEST_CARRIER exact copy failed: {copied}"));
    }
    Ok(bytes)
}

/// SENS-owned Ukrainian API docs cross only root Zig's opaque exact-byte ABI.
/// No Rust include_str! or native source-file read may bypass the corridor.
pub fn uk_docs_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_uk_docs_bytes_copy(
            std::ptr::NonNull::<u8>::dangling().as_ptr(), 0
        )
    };
    if required <= 0 {
        return Err("ZIG_UK_DOCS_CARRIER invalid source length".into());
    }
    let len = usize::try_from(required)
        .map_err(|_| "ZIG_UK_DOCS_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_UK_DOCS_CARRIER source exceeds host byte limit".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe {
        asset_ffi::sens_zig_uk_docs_bytes_copy(bytes.as_mut_ptr(), bytes.len())
    };
    if copied != required {
        return Err(format!("ZIG_UK_DOCS_CARRIER byte copy rejected: code={copied}"));
    }
    Ok(bytes)
}

/// Точні байти lib/unify.lisp через Zig, без Rust include_str! чи семантичної таблиці.
pub fn unify_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_unify_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_UNIFY_CARRIER invalid byte length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_UNIFY_CARRIER length overflow")?;
    // Межа пам'яті хоста, а не закон домену чи допуск виконання SENS.
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_UNIFY_CARRIER host byte limit exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_unify_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_UNIFY_CARRIER exact byte copy failed: {copied}"));
    }
    Ok(bytes)
}

/// lib/reason.lisp source over the sterile Zig byte corridor; no Rust source
/// embedding and no authority to change SENS identities or execution law.
pub fn reason_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_reason_bytes_copy(
            std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_REASON_CARRIER invalid source byte length".into());
    }
    let len = usize::try_from(required)
        .map_err(|_| "ZIG_REASON_CARRIER source length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_REASON_CARRIER host byte limit exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe {
        asset_ffi::sens_zig_reason_bytes_copy(bytes.as_mut_ptr(), bytes.len())
    };
    if copied != required {
        return Err(format!("ZIG_REASON_CARRIER exact byte copy failed: {copied}"));
    }
    Ok(bytes)
}

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

/// Physical-only D1..D10 coordinate check through the same sterile Zig ABI.
/// A valid D10 word is data, never an executable SENS function or numeric value.
/// The ordinary T5 ingest and D1..D9 executable profile are unaffected.
pub fn validate_t5_coordinates(bytes: &[u8]) -> Result<(), String> {
    version()?;
    if unsafe { sens_zig_t5_validate_coordinates(bytes.as_ptr(), bytes.len()) } != 0 {
        return Err("Zig D1..D10 coordinate-only physical validation rejected".into());
    }
    Ok(())
}

/// Єдина механічна проєкція SENS exact-width слів у caller-owned BE3.
/// [width, payload-MSB, payload-LSB] — байти ABI, НЕ фізичний T5/E1
/// і НЕ визначення значення або викличності домену.
fn exact_words_to_be3(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    let capacity = words.len().checked_mul(3)
        .ok_or("Zig BE3 input length overflow")?;
    let mut be3 = Vec::with_capacity(capacity);
    for word in words {
        let width = u8::try_from(word.width())
            .map_err(|_| "Zig BE3 width exceeds one-byte ABI range")?;
        if width == 0 || width > 9 {
            return Err(format!("Zig BE3 unsupported exact word width={width}"));
        }
        let bits = word.packed_bits();
        if (bits as u32) >= (1u32 << width) {
            return Err(format!("Zig BE3 payload exceeds declared width={width}"));
        }
        be3.extend_from_slice(&[width, (bits >> 8) as u8, bits as u8]);
    }
    Ok(be3)
}

pub fn encode_t5_direct(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() {
        return Err("Zig physical T5 cannot encode an empty record".into());
    }
    let semantic_trits = words
        .iter()
        .try_fold(0usize, |n, word| n.checked_add(word.width()))
        .ok_or("Zig T5 semantic bit count overflow")?;
    let used_trits = semantic_trits
        .checked_add(words.len() - 1)
        .ok_or("Zig T5 separator count overflow")?;
    let physical_capacity = used_trits.checked_add(4).ok_or("Zig T5 byte count overflow")? / 5;
    let be3 = exact_words_to_be3(words)?;
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
    let be3 = exact_words_to_be3(words)?;
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
    // Transport egress must not publish bytes before Zig independently
    // restores the same exact SENS coordinates via the existing ABI v2.
    // No Rust E1 physical encoder/decoder or SENS semantic re-evaluation.
    let restored = decode_e1_words(&output)?;
    require_same_exact_words(words, &restored)?;
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
    // Never report "no saving" for an unvalidated physical carrier.
    // Even an oversized T5 input must cross the sterile Zig validator.
    validate_t5(t5)?;
    if t5.len() > 16 {
        return Ok(None);
    }
    let mut bytes = vec![0u8; 16];
    let len = unsafe { sens_zig_f3c_pack(t5.as_ptr(), t5.len(), bytes.as_mut_ptr(), bytes.len()) };
    if len == -3 {
        return Ok(None);
    }
    // Fail closed on non-positive, capacity overreport, or non-smaller framing.
    // Zig may never claim more bytes than the caller-owned buffer.
    if len <= 0 || usize::try_from(len).ok().filter(|&n| n < t5.len() && n <= bytes.len()).is_none()
    {
        return Err(format!("Zig F3C pack rejected: code={len}"));
    }
    bytes.truncate(len as usize);
    Ok(Some(bytes))
}

pub fn decode_f3(carrier: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut output = vec![0u8; 16];
    let len = unsafe {
        sens_zig_f3c_unpack(carrier.as_ptr(), carrier.len(), output.as_mut_ptr(), output.len())
    };
    // Fail closed on non-positive or capacity overreport before any truncate.
    if len <= 0 || usize::try_from(len).ok().filter(|&n| n <= output.len()).is_none() {
        return Err(format!("explicit Zig F3C rejected: code={len}"));
    }
    output.truncate(len as usize);
    validate_t5(&output)?;
    Ok(output)
}

#[cfg(test)]
mod zig_exact_egress_tests {
    use super::{decode_e1_words, decode_f3, decode_t5_words, encode_e1_direct, encode_f3, encode_t5_direct, exact_words_to_be3, require_same_exact_words, validate_t5, validate_t5_coordinates};

    fn words(source: &str) -> Vec<sens::BinarySourceWord> {
        sens::parse_binary_source_words(source)
            .expect("точні двійкові слова")
            .into_iter()
            .map(|token| token.word)
            .collect()
    }

    #[test]
    fn coordinate_d10_is_zig_physical_data_not_executable_t5() {
        // The 10 exact zero bits encode as two T5 bytes. This is a
        // coordinate-only Zig witness; Rust never decodes their meaning.
        let d10 = [0x00, 0x00];
        validate_t5_coordinates(&d10).expect("D10 exact physical coordinate");
        assert!(validate_t5(&d10).is_err(), "D10 never enters executable D9");

        // D1:1 is valid in both physical profiles.
        let d1 = [0xa1];
        validate_t5_coordinates(&d1).expect("D1 coordinate");
        validate_t5(&d1).expect("D1 ordinary carrier");

        // D11=eleven exact zero bits and canonical tail, or bad trits,
        // is never accepted as D10 physical data.
        for invalid in [&[0x00, 0x00, 0x50][..], &[0xff][..], &[][..]] {
            assert!(validate_t5_coordinates(invalid).is_err(),
                "invalid D10 coordinate candidate: {invalid:?}");
        }
    }

    #[test]
    fn f3c_no_saving_never_bypasses_zig_t5_physical_validation() {
        // Nine D9 coordinates need >16 canonical T5 bytes, with leading
        // zeros intact. Only Zig decides their physical validity.
        let long_words = words(&["010101000"; 9].join(" "));
        let long_t5 = encode_t5_direct(&long_words).expect("Zig canonical T5");
        assert!(long_t5.len() > 16);
        assert!(encode_f3(&long_t5).expect("valid large Zig T5").is_none());

        // Same length, but an out-of-range ternary byte is NEVER benign
        // "F3C not smaller": reject it before the length-based decision.
        let mut corrupt = long_t5.clone();
        corrupt[0] = 0xf3;
        let failure = encode_f3(&corrupt).expect_err("invalid large T5 must fail closed");
        assert!(failure.contains("Zig physical T5 rejected"));

        // Positive tiny F3C stays on Zig's byte-exact physical path.
        let small = encode_t5_direct(&words("10 001 00 000 01"))
            .expect("canonical small T5");
        assert_eq!(small, [0x63, 0x89, 0x06, 0xa1]);
        let packed = encode_f3(&small)
            .expect("Zig F3C validation and encode")
            .expect("tiny F3C should save physical bytes");
        assert_eq!(packed, [0xf3, 0x40, 0x60]);
    }

    #[test]
    fn f3c_pack_unpack_reject_overreported_lengths_contract() {
        // Production paths must bound Zig-reported counts before truncate.
        // Source-level contract mirror of the live encode_f3/decode_f3 bodies
        // (same usize::try_from + capacity filter pattern used by E1).
        let src = include_str!("zig_transport.rs");
        let pack = src
            .split("pub fn encode_f3(")
            .nth(1)
            .and_then(|s| s.split("pub fn decode_f3(").next())
            .expect("encode_f3 route");
        assert!(
            pack.contains("usize::try_from(len)")
                && pack.contains("n <= bytes.len()")
                && pack.contains("n < t5.len()"),
            "encode_f3 must reject overreported / non-smaller F3C lengths before truncate"
        );
        let unpack = src
            .split("pub fn decode_f3(")
            .nth(1)
            .and_then(|s| s.split("#[cfg(test)]").next())
            .expect("decode_f3 route");
        assert!(
            unpack.contains("usize::try_from(len)")
                && unpack.contains("n <= output.len()"),
            "decode_f3 must reject overreported F3C lengths before truncate"
        );

        // Live golden still round-trips under the stricter bound.
        let small = encode_t5_direct(&words("10 001 00 000 01")).expect("T5");
        let packed = encode_f3(&small).expect("pack").expect("saves");
        assert_eq!(packed, [0xf3, 0x40, 0x60]);
        let recovered = decode_f3(&packed).expect("unpack validates");
        assert_eq!(recovered, small);
    }

    #[test]
    fn one_mechanical_be3_projection_for_t5_and_e1() {
        // D1:1, D2:01, D3:001 and D9:010101000 are DISTINCT exact words.
        let original = words("1 01 001 010101000");
        let be3 = exact_words_to_be3(&original).expect("single BE3 ABI projection");
        assert_eq!(be3, [1, 0, 1, 2, 0, 1, 3, 0, 1, 9, 0, 0xa8]);
        let t5 = encode_t5_direct(&original).expect("Zig physical T5");
        let e1 = encode_e1_direct(&original).expect("Zig physical E1");
        require_same_exact_words(&original, &decode_t5_words(&t5).unwrap()).unwrap();
        require_same_exact_words(&original, &decode_e1_words(&e1).unwrap()).unwrap();

        // Both production egress paths must call ONE helper and must not
        // separately rebuild BE3 or use Rust physical encoders.
        let source = include_str!("zig_transport.rs");
        for name in ["encode_t5_direct", "encode_e1_direct"] {
            let start = source.find(&format!("pub fn {name}(")).unwrap();
            let body = &source[start..];
            let end = body.find("\n}\n").unwrap();
            let route = &body[..end];
            assert!(route.contains("exact_words_to_be3(words)?"), "{name}");
            assert!(!route.contains("be3.push("), "{name}");
            assert!(!route.contains("be3.extend_from_slice("), "{name}");
            assert!(!route.contains("sens::encode_ternary_words("), "{name}");
            assert!(!route.contains("sens::envelope_e1::encode("), "{name}");
        }
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
    fn e1_egress_reenters_only_zig_and_preserves_exact_domain_words() {
        // W1:1 and W2:01 have the same low payload but different identities.
        // D9 retains nine physical bits including its leading zero.
        let source = words("1 01 001 010101000");
        let frame = encode_e1_direct(&source)
            .expect("SENS exact words -> Zig E1 encode -> Zig E1 decode");
        let restored = decode_e1_words(&frame).expect("canonical Zig E1 ingress");
        require_same_exact_words(&source, &restored)
            .expect("byte-for-byte exact width and payload preservation");
        assert_eq!(source.len(), restored.len());
        assert_eq!(restored.iter().copied().map(sens::BinarySourceWord::width)
            .collect::<Vec<_>>(), [1, 2, 3, 9]);

        // CRC mutation must fail before any Rust host can admit SENS meaning.
        let mut damaged = frame.clone();
        let last = damaged.len() - 1;
        damaged[last] ^= 1;
        assert!(decode_e1_words(&damaged).is_err());

        // A carrier can be canonical yet represent the WRONG exact words.
        // Fail closed on each domain-width, payload and word-count mismatch.
        assert!(require_same_exact_words(&source, &words("01 01 001 010101000"))
            .unwrap_err().contains("expected_width=1"));
        assert!(require_same_exact_words(&source, &words("0 01 001 010101000"))
            .unwrap_err().contains("index=0"));
        assert!(require_same_exact_words(&source, &words("1 01 001"))
            .unwrap_err().contains("word_count"));

        // Scope proof: this production egress has neither Rust E1 codec
        // nor a silent reference fallback after Zig produces bytes.
        let code = include_str!("zig_transport.rs");
        let route = code.split("pub fn encode_e1_direct(").nth(1)
            .expect("E1 Zig egress")
            .split("pub fn decode_e1_words(").next().expect("next route");
        assert!(route.contains("sens_zig_e1_encode_be3("));
        assert!(route.contains("decode_e1_words(&output)?"));
        assert!(route.contains("require_same_exact_words(words, &restored)?"));
        assert!(!route.contains("sens::envelope_e1::encode"));
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
