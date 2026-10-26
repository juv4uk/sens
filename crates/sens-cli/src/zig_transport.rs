//! Стерильний ABI v2 між SENS та будь-яким хостом для фізичних T5M/T5/F3C/E1.
//! Owner law: Zig is the turnstile, not the registry; SENS decides meaning;
//! Rust holds opaque bytes. No local T5/E1 algorithm lives in this module.

// Root-Zig opaque asset copies are a separate adapter, NOT codec ABI v2.
#[path = "zig_transport_assets.rs"]
mod asset_ffi;

// Native Zig archive is named explicitly because Cargo's build-script link-lib
// directive attaches to the library target once src/lib.rs exists. Other binary
// targets still include this host-neutral transport module independently.
// This is linking only; no Rust implementation or fallback is introduced.
#[link(name = "sens_zig_transport", kind = "static")]
unsafe extern "C" {
    fn sens_zig_codec_abi_version() -> u32;
    fn sens_zig_bitpack_fields(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_t5m_validate(input: *const u8, len: usize) -> i32;
    fn sens_zig_t5m_encode_be3(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_t5m_decode_be3(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_t5m_encode_words(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_t5m_decode_words(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_t5_validate(input: *const u8, len: usize) -> i32;
    // Coordinate-only D1..D10 physical validation; no runnable D10 admission.
    fn sens_zig_t5_validate_coordinates(input: *const u8, len: usize) -> i32;
    fn sens_zig_t5_encode_be3(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_t5_decode_be3(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_e1_encode_be3(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_e1_decode_be3(
        input: *const u8,
        byte_len: usize,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    fn sens_zig_f3c_pack(input: *const u8, len: usize, output: *mut u8, capacity: usize) -> isize;
    fn sens_zig_f3c_unpack(input: *const u8, len: usize, output: *mut u8, capacity: usize)
                           -> isize;
}


/// Pack caller-owned exact-width raw fields through Zig's canonical raw
/// MSB-first bitpacker. Each nine-byte record is [width:u8][value:u64 BE].
/// This is a mechanical payload helper, not SENS semantic admission.
pub fn pack_raw_bit_fields(records: &[u8]) -> Result<Vec<u8>, String> {
    if records.is_empty() {
        return Err("Zig raw bitpack rejects an empty field schema".into());
    }
    let queried = unsafe {
        sens_zig_bitpack_fields(
            records.as_ptr(),
            records.len(),
            std::ptr::NonNull::<u8>::dangling().as_ptr(),
            0,
        )
    };
    let required = usize::try_from(queried)
        .ok()
        .filter(|&size| size > 0)
        .ok_or_else(|| format!("Zig raw bitpack size query rejected: {queried}"))?;
    let mut output = vec![0u8; required];
    let written = unsafe {
        sens_zig_bitpack_fields(
            records.as_ptr(),
            records.len(),
            output.as_mut_ptr(),
            output.len(),
        )
    };
    if written != queried {
        return Err(format!("Zig raw bitpack length mismatch: expected={queried} actual={written}"));
    }
    Ok(output)
}

fn version() -> Result<(), String> {
    if unsafe { sens_zig_codec_abi_version() } != 2 {
        return Err("Zig codec C ABI version mismatch".into());
    }
    Ok(())
}

/// Exact-width physical word for the Zig T5M bridge. Each bit is one byte
/// whose value is 0 or 1; it carries no domain identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExactT5MWord {
    pub width: usize,
    pub bits: Vec<u8>,
}

impl ExactT5MWord {
    pub fn new(width: usize, bits: Vec<u8>) -> Result<Self, String> {
        if width == 0 || bits.len() != width || bits.iter().any(|&bit| bit > 1) {
            return Err(
                "точне слово T5M потребує додатну ширину й рівно стільки байтів-бітів 0/1".into(),
            );
        }
        Ok(Self { width, bits })
    }

    pub fn width(&self) -> usize {
        self.width
    }
    pub fn bits(&self) -> &[u8] {
        &self.bits
    }
}

/// Кодує точні слова через фізичний кодек Zig T5M без стелі BE3 W1–W9.
pub fn encode_t5m_exact_words(words: &[ExactT5MWord]) -> Result<Vec<u8>, String> {
    encode_t5m_exact_words_and_restore(words).map(|(physical, _)| physical)
}

/// Кодує, один раз декодує через Zig для перевірки й повертає відновлені слова.
/// REPL може використати той самий результат зворотного шляху без повторного декодування.
pub fn encode_t5m_exact_words_and_restore(
    words: &[ExactT5MWord],
) -> Result<(Vec<u8>, Vec<ExactT5MWord>), String> {
    version()?;
    if words.is_empty() {
        return Err("Zig T5M cannot encode an empty word sequence".into());
    }
    if words.iter().any(|word| {
        word.width == 0 || word.bits.len() != word.width || word.bits.iter().any(|&bit| bit > 1)
    }) {
        return Err("точне слово T5M має містити рівно width байтів зі значенням 0/1".into());
    }
    let trits = words
        .iter()
        .try_fold(words.len() - 1, |n, word| n.checked_add(word.width))
        .ok_or("exact T5M trit count overflow")?;
    let physical_capacity = trits
        .checked_add(4)
        .ok_or("exact T5M byte count overflow")?
        / 5;
    let record_capacity = words
        .iter()
        .try_fold(0usize, |n, word| n.checked_add(4)?.checked_add(word.width))
        .ok_or("exact T5M ABI record length overflow")?;
    let mut records = Vec::new();
    records
        .try_reserve_exact(record_capacity)
        .map_err(|_| "не вдалося виділити буфер записів T5M")?;
    for word in words {
        let width = u32::try_from(word.width).map_err(|_| "exact T5M word exceeds u32 width")?;
        records.extend_from_slice(&width.to_be_bytes());
        records.extend_from_slice(&word.bits);
    }
    let mut physical = vec![0u8; physical_capacity];
    let written = unsafe {
        sens_zig_t5m_encode_words(
            records.as_ptr(),
            records.len(),
            physical.as_mut_ptr(),
            physical.len(),
        )
    };
    if written <= 0
        || usize::try_from(written)
        .ok()
        .filter(|&n| n <= physical.len())
        .is_none()
    {
        return Err(format!("Zig exact T5M encode rejected: code={written}"));
    }
    physical.truncate(written as usize);
    let restored = decode_t5m_exact_words(&physical)?;
    if restored != words {
        return Err("Zig T5M змінив ширину слова або його біти".into());
    }
    Ok((physical, restored))
}

/// Декодує T5M через Zig зі збереженням довільних точних додатних ширин.
pub fn decode_t5m_exact_words(physical: &[u8]) -> Result<Vec<ExactT5MWord>, String> {
    version()?;
    validate_t5m(physical)?;
    let trits = physical
        .len()
        .checked_mul(5)
        .ok_or("exact T5M trit count overflow")?;
    let capacity =
        max_t5_decode_record_bytes(trits).ok_or("exact T5M decoded capacity overflow")?;
    // Zig writes exactly the returned number of initialized record bytes.
    // Keep the reserved tail uninitialized: zero-filling a 5x-trit buffer
    // touched pages the decoder never used and inflated peak RSS.
    let mut records = Vec::<u8>::with_capacity(capacity);
    let written = unsafe {
        sens_zig_t5m_decode_words(
            physical.as_ptr(),
            physical.len(),
            records.as_mut_ptr(),
            records.capacity(),
        )
    };
    let len = usize::try_from(written)
        .ok()
        .filter(|&n| n > 0 && n <= records.capacity())
        .ok_or_else(|| format!("Zig exact T5M decode rejected: code={written}"))?;
    // SAFETY: Zig's ABI returns `need` only after writing every byte in
    // `dst[0..need]`; the checked capacity above bounds that initialized range.
    unsafe { records.set_len(len) };
    let mut words = Vec::new();
    let mut offset = 0usize;
    while offset < records.len() {
        if records.len() - offset < 4 {
            return Err("Zig exact T5M returned truncated width".into());
        }
        let width = u32::from_be_bytes(
            records[offset..offset + 4]
                .try_into()
                .expect("four-byte width"),
        ) as usize;
        offset += 4;
        let end = offset
            .checked_add(width)
            .ok_or("Zig exact T5M width overflow")?;
        let bits = records
            .get(offset..end)
            .ok_or("Zig exact T5M returned truncated word")?
            .to_vec();
        words.push(ExactT5MWord::new(width, bits)?);
        offset = end;
    }
    if words.is_empty() {
        return Err("Zig exact T5M returned no words".into());
    }
    Ok(words)
}

/// Upper bound for Zig's `[u32 width][one byte per bit]` records. Each word
/// consumes at least one data trit and each adjacent pair needs a separator,
/// so at most ceil(trits / 2) records can occur. Padding is included in the
/// supplied physical trit count and therefore only makes this conservative.
fn max_t5_decode_record_bytes(trits: usize) -> Option<usize> {
    let max_words = trits / 2 + trits % 2;
    trits.checked_add(max_words.checked_mul(3)?)?.checked_add(1)
}

// SENS defines REPL/read/identity; these functions carry ONLY untouched bytes.
// The two-call ABI checks size before writing and fails closed on short copies.
fn opaque_zig_asset(
    copy: unsafe extern "C" fn(*mut u8, usize) -> isize,
    label: &str,
) -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe { copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0) };
    if required <= 0 {
        return Err(format!("{label}: no Zig-owned source bytes ({required})"));
    }
    let len =
        usize::try_from(required).map_err(|_| format!("{label}: Zig source length overflow"))?;
    if len > 8 * 1024 * 1024 {
        return Err(format!("{label}: exceeds host byte bound"));
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { copy(bytes.as_mut_ptr(), len) };
    if copied != required {
        return Err(format!(
            "{label}: incomplete Zig byte copy expected={required} actual={copied}"
        ));
    }
    Ok(bytes)
}

/// Physical T5M bytes for the SENS-owned REPL core; no source text crosses to Rust.
pub fn repl_core_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_repl_core_t5m_bytes_copy,
        "ZIG_SENS_REPL_T5M",
    )
}

/// Physical T5M bytes for the SENS-owned metacircular evaluator.
pub fn meta_eval_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_meta_eval_t5m_bytes_copy,
        "ZIG_META_EVAL_T5M",
    )
}

/// Physical T5M bytes for the REPL persistent-vector library.
pub fn repl_persistent_vector_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_repl_persistent_vector_t5m_bytes_copy,
        "ZIG_REPL_PERSISTENT_VECTOR_T5M",
    )
}

/// Physical T5M bytes for the REPL epistemic library.
pub fn repl_epistemic_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_repl_epistemic_t5m_bytes_copy,
        "ZIG_REPL_EPISTEMIC_T5M",
    )
}

/// Physical T5M bytes for the REPL persistent-map library.
pub fn persistent_map_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_repl_persistent_map_t5m_bytes_copy,
        "ZIG_REPL_PERSISTENT_MAP_T5M",
    )
}

/// F6 world library as an opaque physical T5M asset owned by Zig.
pub fn f6_world_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_f6_world_t5m_bytes_copy,
        "ZIG_F6_WORLD_T5M",
    )
}

/// F6 content-store library as an opaque physical T5M asset owned by Zig.
pub fn f6_content_store_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_f6_content_store_t5m_bytes_copy,
        "ZIG_F6_CONTENT_STORE_T5M",
    )
}

/// F6 filesystem library as an opaque physical T5M asset owned by Zig.
pub fn f6_lisp_fs_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_f6_lisp_fs_t5m_bytes_copy,
        "ZIG_F6_LISP_FS_T5M",
    )
}

/// F6 producer witness as an opaque physical T5M asset owned by Zig.
pub fn f6_producer_witness_t5m_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_f6_producer_witness_t5m_bytes_copy,
        "ZIG_F6_PRODUCER_WITNESS_T5M",
    )
}

/// Ordered physical T5M assets for the REPL's reasoning prerequisites.
/// Rust receives exact bytes; the SENS binary reader/evaluator owns meaning.
pub fn repl_reasoning_t5m_assets() -> Result<Vec<(&'static str, Vec<u8>)>, String> {
    Ok(vec![
        (
            "unify",
            opaque_zig_asset(
                asset_ffi::sens_zig_repl_unify_t5m_bytes_copy,
                "ZIG_REPL_UNIFY_T5M",
            )?,
        ),
        (
            "reason",
            opaque_zig_asset(
                asset_ffi::sens_zig_repl_reason_t5m_bytes_copy,
                "ZIG_REPL_REASON_T5M",
            )?,
        ),
        (
            "forward",
            opaque_zig_asset(
                asset_ffi::sens_zig_repl_forward_t5m_bytes_copy,
                "ZIG_REPL_FORWARD_T5M",
            )?,
        ),
        (
            "knowledge",
            opaque_zig_asset(
                asset_ffi::sens_zig_repl_knowledge_t5m_bytes_copy,
                "ZIG_REPL_KNOWLEDGE_T5M",
            )?,
        ),
    ])
}

/// Opaque D9 string-append source bytes carried through the Zig root ABI.
pub fn d9_string_append_source_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_d9_string_append_bytes_copy,
        "ZIG_D9_STRING_APPEND",
    )
}

/// Перечитує актуальний Guard-довідник через Zig; шлях зафіксований у Zig,
/// Rust не відкриває файл сам і не кешує його між викликами.
pub fn guard_reference_source_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_guard_reference_bytes_copy,
        "ZIG_GUARD_REFERENCE",
    )
}

/// Механічний інваріант SENS ↔ Zig: кількість, ширина, біти.
/// Не визначає значення функцій і не замінює SENS-семантичний оракул.
/// Retrieves opaque physical linter T5M through the sterile Zig C ABI.
/// Rust never opens the Lisp source and Zig performs no semantic work.
pub fn linter_t5m_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_linter_t5m_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_LINTER_T5M_CARRIER invalid physical length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_LINTER_T5M_CARRIER length overflow")?;
    // Host memory bound. This is not a SENS domain/semantic admission threshold.
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_LINTER_T5M_CARRIER exceeds host byte limit".into());
    }
    let mut bytes = vec![0u8; len];
    let copied =
        unsafe { asset_ffi::sens_zig_linter_t5m_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_LINTER_T5M_CARRIER byte copy rejected: code={copied}"
        ));
    }
    Ok(bytes)
}

/// Exact opaque project contract via Zig ABI. Zig does not interpret it.
pub fn contract_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_contract_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_CONTRACT_CARRIER invalid length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_CONTRACT_CARRIER overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_CONTRACT_CARRIER host byte cap".into());
    }
    let mut bytes = vec![0u8; len];
    let copied =
        unsafe { asset_ffi::sens_zig_contract_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_CONTRACT_CARRIER mismatch: {copied}"));
    }
    Ok(bytes)
}

/// Opaque Sanskrit REPL source from the root Zig module, without Rust file access.
pub fn sanskrit_surface_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_sanskrit_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_SANSKRIT_CARRIER invalid length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_SANSKRIT_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_SANSKRIT_CARRIER host byte limit".into());
    }
    let mut bytes = vec![0u8; len];
    let copied =
        unsafe { asset_ffi::sens_zig_sanskrit_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_SANSKRIT_CARRIER copy mismatch: {copied}"));
    }
    Ok(bytes)
}

/// Opaque full-Ukrainian REPL source; Zig is only a byte corridor.
#[cfg(test)]
pub fn ukr_surface_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_ukr_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_UKR_CARRIER invalid length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_UKR_CARRIER overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_UKR_CARRIER host limit".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_ukr_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_UKR_CARRIER copy mismatch: {copied}"));
    }
    Ok(bytes)
}

/// Compact Ukrainian source goes through sterile Zig byte transport only.
#[cfg(test)]
pub fn uk_surface_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_uk_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_UK_CARRIER invalid length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_UK_CARRIER size overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_UK_CARRIER host bound".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_uk_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_UK_CARRIER mismatch: {copied}"));
    }
    Ok(bytes)
}

/// Release distribution JSON is copied as opaque bytes from root Zig 0.16.
/// Rust may validate the manifest protocol but cannot embed project sources.
pub fn islands_manifest_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_islands_manifest_bytes_copy(
            std::ptr::NonNull::<u8>::dangling().as_ptr(),
            0,
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
    let copied =
        unsafe { asset_ffi::sens_zig_islands_manifest_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_ISLANDS_MANIFEST_CARRIER exact copy failed: {copied}"
        ));
    }
    Ok(bytes)
}

/// SENS-owned Ukrainian API docs cross only root Zig's opaque exact-byte ABI.
/// No Rust include_str! or native source-file read may bypass the corridor.
pub fn uk_docs_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_uk_docs_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_UK_DOCS_CARRIER invalid source length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_UK_DOCS_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_UK_DOCS_CARRIER source exceeds host byte limit".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_uk_docs_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_UK_DOCS_CARRIER byte copy rejected: code={copied}"
        ));
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
        return Err(format!(
            "ZIG_UNIFY_CARRIER exact byte copy failed: {copied}"
        ));
    }
    Ok(bytes)
}

/// lib/reason.lisp source over the sterile Zig byte corridor; no Rust source
/// embedding and no authority to change SENS identities or execution law.
pub fn reason_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_reason_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_REASON_CARRIER invalid source byte length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_REASON_CARRIER source length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_REASON_CARRIER host byte limit exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_reason_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_REASON_CARRIER exact byte copy failed: {copied}"
        ));
    }
    Ok(bytes)
}

/// Opaque lib/forward.lisp carried by Zig's exact two-call C ABI.
/// SENS alone determines execution, and historical source debt stays unchanged.
pub fn forward_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_forward_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_FORWARD_CARRIER invalid source byte length".into());
    }
    let len =
        usize::try_from(required).map_err(|_| "ZIG_FORWARD_CARRIER source length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_FORWARD_CARRIER host byte limit exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_forward_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_FORWARD_CARRIER exact byte copy failed: {copied}"
        ));
    }
    Ok(bytes)
}

/// lib/knowledge.lisp original bytes across the sterile Zig asset ABI.
/// Host policy is limited to byte capacity and UTF-8 transport, not semantics.
pub fn knowledge_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_knowledge_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_KNOWLEDGE_CARRIER invalid source length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_KNOWLEDGE_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_KNOWLEDGE_CARRIER host byte cap exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied =
        unsafe { asset_ffi::sens_zig_knowledge_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_KNOWLEDGE_CARRIER byte copy rejected: {copied}"
        ));
    }
    Ok(bytes)
}

/// Project-authored lib/persistent-map.lisp is only opaque bytes at this edge.
/// Root Zig adapter carries them; the host does not interpret source identity.
pub fn persistent_map_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_persistent_map_bytes_copy(
            std::ptr::NonNull::<u8>::dangling().as_ptr(),
            0,
        )
    };
    if required <= 0 {
        return Err("ZIG_PERSISTENT_MAP_CARRIER invalid length".into());
    }
    let len =
        usize::try_from(required).map_err(|_| "ZIG_PERSISTENT_MAP_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_PERSISTENT_MAP_CARRIER host byte cap exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied =
        unsafe { asset_ffi::sens_zig_persistent_map_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_PERSISTENT_MAP_CARRIER byte-copy mismatch: {copied}"
        ));
    }
    Ok(bytes)
}

/// Root Zig copies the World source byte-for-byte; SENS alone evaluates it.
pub fn world_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_world_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_WORLD_CARRIER invalid length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_WORLD_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_WORLD_CARRIER host byte cap exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_world_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_WORLD_CARRIER byte-copy mismatch: {copied}"));
    }
    Ok(bytes)
}

/// Original F6 filesystem source is byte-exact through Zig, never Rust include.
pub fn lisp_fs_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_lisp_fs_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_F6_LISP_FS_CARRIER invalid source length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_F6_LISP_FS_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_F6_LISP_FS_CARRIER host byte cap exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { asset_ffi::sens_zig_lisp_fs_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_F6_LISP_FS_CARRIER byte copy rejected: {copied}"
        ));
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

pub fn validate_t5m(bytes: &[u8]) -> Result<(), String> {
    version()?;
    if unsafe { sens_zig_t5m_validate(bytes.as_ptr(), bytes.len()) } != 0 {
        return Err("Zig physical T5M rejected; no SENS execution".into());
    }
    Ok(())
}

fn validate_legacy_t5(bytes: &[u8]) -> Result<(), String> {
    version()?;
    if unsafe { sens_zig_t5_validate(bytes.as_ptr(), bytes.len()) } != 0 {
        return Err("legacy T5 physical carrier rejected".into());
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
    let capacity = words
        .len()
        .checked_mul(3)
        .ok_or("Zig BE3 input length overflow")?;
    let mut be3 = Vec::with_capacity(capacity);
    for word in words {
        let width =
            u8::try_from(word.width()).map_err(|_| "Zig BE3 width exceeds one-byte ABI range")?;
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

pub fn encode_t5m_direct(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() {
        return Err("Zig physical T5M cannot encode an empty record".into());
    }
    let semantic_trits = words
        .iter()
        .try_fold(0usize, |n, word| n.checked_add(word.width()))
        .ok_or("Zig T5 semantic bit count overflow")?;
    let used_trits = semantic_trits
        .checked_add(words.len() - 1)
        .ok_or("Zig T5 separator count overflow")?;
    let physical_capacity = used_trits
        .checked_add(4)
        .ok_or("Zig T5M byte count overflow")?
        / 5;
    let be3 = exact_words_to_be3(words)?;
    let mut bytes = vec![0u8; physical_capacity];
    let len = unsafe {
        sens_zig_t5m_encode_be3(be3.as_ptr(), be3.len(), bytes.as_mut_ptr(), bytes.len())
    };
    if len < 0 || usize::try_from(len).ok() != Some(bytes.len()) {
        return Err(format!("Zig physical T5M encode rejected: code={len}"));
    }
    // Обидва напрями проходять тільки стерильний Zig ABI, без Rust T5 codec.
    let restored = decode_t5m_words(&bytes)?;
    require_same_exact_words(words, &restored)?;
    Ok(bytes)
}

fn encode_legacy_t5(words: &[sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
    version()?;
    if words.is_empty() {
        return Err("legacy T5 cannot encode empty record".into());
    }
    let trits = words
        .iter()
        .try_fold(words.len() - 1, |n, word| n.checked_add(word.width()))
        .ok_or("legacy T5 trit count overflow")?;
    let capacity = trits.checked_add(4).ok_or("legacy T5 capacity overflow")? / 5;
    let be3 = exact_words_to_be3(words)?;
    let mut bytes = vec![0u8; capacity];
    let written =
        unsafe { sens_zig_t5_encode_be3(be3.as_ptr(), be3.len(), bytes.as_mut_ptr(), bytes.len()) };
    if written < 0 || usize::try_from(written).ok() != Some(bytes.len()) {
        return Err(format!("legacy T5 Zig encode rejected: code={written}"));
    }
    Ok(bytes)
}

pub fn verify_t5m_encoding(
    words: &[sens::BinarySourceWord],
    expected_bytes: &[u8],
) -> Result<Vec<u8>, String> {
    let bytes = encode_t5m_direct(words)?;
    if bytes != expected_bytes {
        return Err("Zig T5M and admitted SENS reference differ at a physical byte".into());
    }
    Ok(bytes)
}

pub fn decode_t5m_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    validate_t5m(bytes)?;
    let trits = bytes
        .len()
        .checked_mul(5)
        .ok_or("T5M input length overflow")?;
    let max_words = trits.checked_add(1).ok_or("T5M word count overflow")? / 2;
    let capacity = max_words
        .checked_mul(3)
        .ok_or("T5M BE3 capacity overflow")?;
    let mut be3 = vec![0u8; capacity];
    let written = unsafe {
        sens_zig_t5m_decode_be3(bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len())
    };
    if written <= 0
        || usize::try_from(written)
        .ok()
        .filter(|&n| n <= be3.len())
        .is_none()
        || written % 3 != 0
    {
        if let Ok(exact_words) = decode_t5m_exact_words(bytes) {
            let mut widths: Vec<usize> = exact_words
                .iter()
                .map(|word| word.width)
                .filter(|&width| width > 9)
                .collect();
            widths.sort_unstable();
            widths.dedup();
            if !widths.is_empty() {
                return Err(format!(
                    "Фізичне T5M-декодування зберегло точні ширини слів {widths:?}; застарілий адаптер BinarySourceWord приймає лише W1–W9. Ширина не є доменною identity, тому належність до D1–24+ або викличність не виведено"
                ));
            }
        }
        return Err(format!("Zig physical T5M decode rejected: code={written}"));
    }
    be3.truncate(written as usize);
    let mut words = Vec::with_capacity(be3.len() / 3);
    let (triples, remainder) = be3.as_slice().as_chunks::<3>();
    if !remainder.is_empty() {
        return Err("Zig BE3 output contains a partial triple".into());
    }
    for triple in triples {
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

pub fn decode_legacy_t5_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    validate_legacy_t5(bytes)?;
    let capacity = bytes
        .len()
        .checked_mul(5)
        .and_then(|n| n.checked_add(1))
        .and_then(|n| n.checked_div(2))
        .and_then(|n| n.checked_mul(3))
        .ok_or("legacy T5M BE3 capacity overflow")?;
    let mut be3 = vec![0u8; capacity];
    let written =
        unsafe { sens_zig_t5_decode_be3(bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len()) };
    if written <= 0
        || usize::try_from(written)
        .ok()
        .filter(|&n| n <= be3.len() && n % 3 == 0)
        .is_none()
    {
        return Err(format!("legacy T5 Zig decode rejected: code={written}"));
    }
    be3.truncate(written as usize);
    let mut words = Vec::with_capacity(be3.len() / 3);
    let (triples, remainder) = be3.as_slice().as_chunks::<3>();
    if !remainder.is_empty() {
        return Err("Zig BE3 output contains a partial triple".into());
    }
    for triple in triples {
        let width = triple[0];
        let payload = (u16::from(triple[1]) << 8) | u16::from(triple[2]);
        if width < 9 && payload > u16::from(u8::MAX) {
            return Err("legacy T5 BE3 payload exceeds declared narrow width".into());
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
            .ok_or_else(|| format!("legacy T5 BE3 invalid exact word width={width}"))?;
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
    if written <= 0
        || usize::try_from(written)
        .ok()
        .filter(|&n| n <= output.len())
        .is_none()
    {
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
    let written =
        unsafe { sens_zig_e1_decode_be3(bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len()) };
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
    let (triples, remainder) = be3.as_slice().as_chunks::<3>();
    if !remainder.is_empty() {
        return Err("Zig BE3 output contains a partial triple".into());
    }
    for triple in triples {
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
    // F3C is the explicit legacy-T5 compact container. Convert the current
    // T5M words through Zig before asking its legacy physical optimizer.
    let logical_words = decode_t5m_words(t5)?;
    let legacy = encode_legacy_t5(&logical_words)?;
    if legacy.len() > 16 {
        return Ok(None);
    }
    let mut bytes = vec![0u8; 16];
    let len = unsafe {
        sens_zig_f3c_pack(
            legacy.as_ptr(),
            legacy.len(),
            bytes.as_mut_ptr(),
            bytes.len(),
        )
    };
    if len == -3 {
        return Ok(None);
    }
    // Fail closed on non-positive, capacity overreport, or non-smaller framing.
    // Zig may never claim more bytes than the caller-owned buffer.
    if len <= 0
        || usize::try_from(len)
        .ok()
        .filter(|&n| n < legacy.len() && n <= bytes.len())
        .is_none()
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
        sens_zig_f3c_unpack(
            carrier.as_ptr(),
            carrier.len(),
            output.as_mut_ptr(),
            output.len(),
        )
    };
    // Fail closed on non-positive or capacity overreport before any truncate.
    if len <= 0
        || usize::try_from(len)
        .ok()
        .filter(|&n| n <= output.len())
        .is_none()
    {
        return Err(format!("explicit Zig F3C rejected: code={len}"));
    }
    output.truncate(len as usize);
    let words = decode_legacy_t5_words(&output)?;
    encode_t5m_direct(&words)
}

/// SENS Content Store source crosses the sterile Zig corridor as exact bytes.
pub fn content_store_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        asset_ffi::sens_zig_content_store_bytes_copy(
            std::ptr::NonNull::<u8>::dangling().as_ptr(),
            0,
        )
    };
    if required <= 0 {
        return Err("ZIG_CONTENT_STORE_CARRIER invalid length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_CONTENT_STORE_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_CONTENT_STORE_CARRIER host byte cap exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied =
        unsafe { asset_ffi::sens_zig_content_store_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_CONTENT_STORE_CARRIER byte-copy mismatch: {copied}"
        ));
    }
    Ok(bytes)
}

/// Returns one SENS-owned domain projection table as opaque Zig-carried bytes.
pub fn domain_table_source_bytes(domain: u8) -> Result<Vec<u8>, String> {
    version()?;
    if !(1..=11).contains(&domain) {
        return Err(format!(
            "ZIG_DOMAIN_TABLE_CARRIER unknown asset index {domain}"
        ));
    }
    let required = unsafe {
        asset_ffi::sens_zig_domain_table_bytes_copy(
            domain,
            std::ptr::NonNull::<u8>::dangling().as_ptr(),
            0,
        )
    };
    if required <= 0 {
        return Err(format!(
            "ZIG_DOMAIN_TABLE_CARRIER invalid length for asset {domain}: {required}"
        ));
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_DOMAIN_TABLE_CARRIER length overflow")?;
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_DOMAIN_TABLE_CARRIER host byte cap exceeded".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe {
        asset_ffi::sens_zig_domain_table_bytes_copy(domain, bytes.as_mut_ptr(), bytes.len())
    };
    if copied != required {
        return Err(format!(
            "ZIG_DOMAIN_TABLE_CARRIER byte-copy mismatch for asset {domain}: {copied}"
        ));
    }
    Ok(bytes)
}

/// Opaque SENS compiler nucleus bytes carried through the Zig root ABI.
pub fn compiler_nucleus_source_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_compiler_nucleus_bytes_copy,
        "ZIG_COMPILER_NUCLEUS_CARRIER",
    )
}

/// Opaque compiler identity corpus bytes carried through the Zig root ABI.
pub fn compiler_identity_corpus_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_compiler_identity_corpus_bytes_copy,
        "ZIG_COMPILER_IDENTITY_CORPUS_CARRIER",
    )
}

/// Opaque compiler authority and structural projection bytes carried by Zig.
pub fn compiler_language_contract_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_compiler_contract_bytes_copy,
        "ZIG_COMPILER_CONTRACT_CARRIER",
    )
}

pub fn compiler_d3_projection_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_compiler_d3_projection_bytes_copy,
        "ZIG_COMPILER_D3_PROJECTION_CARRIER",
    )
}

pub fn compiler_d3_authority_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_compiler_d3_authority_bytes_copy,
        "ZIG_COMPILER_D3_AUTHORITY_CARRIER",
    )
}

pub fn compiler_d4_projection_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_compiler_d4_projection_bytes_copy,
        "ZIG_COMPILER_D4_PROJECTION_CARRIER",
    )
}

pub fn compiler_d4_authority_bytes() -> Result<Vec<u8>, String> {
    opaque_zig_asset(
        asset_ffi::sens_zig_compiler_d4_authority_bytes_copy,
        "ZIG_COMPILER_D4_AUTHORITY_CARRIER",
    )
}

#[cfg(test)]
mod zig_exact_egress_tests {
    use super::{
        decode_e1_words, decode_f3, decode_t5m_exact_words, decode_t5m_words, encode_e1_direct,
        encode_f3, encode_t5m_direct, exact_words_to_be3, require_same_exact_words,
        validate_t5_coordinates, validate_t5m,
    };

    #[test]
    fn live_guard_reference_bytes_cross_only_the_zig_adapter() {
        let bytes = super::guard_reference_source_bytes()
            .expect("Zig reads the current Guard reference source");
        let text = std::str::from_utf8(&bytes).expect("Guard reference is UTF-8");
        assert!(
            text.starts_with("; Guard reference bureau"),
            "unexpected Guard source identity"
        );
        assert!(
            bytes.len() > 1024,
            "reference source unexpectedly truncated"
        );
    }

    fn words(source: &str) -> Vec<sens::BinarySourceWord> {
        sens::parse_binary_source_words(source)
            .expect("точні двійкові слова")
            .into_iter()
            .map(|token| token.word)
            .collect()
    }

    #[test]
    fn compiler_source_assets_cross_zig_byte_exact() {
        let sources = [
            (
                super::compiler_nucleus_source_bytes().unwrap(),
                include_bytes!("../../../lib/compiler-nucleus.lisp").as_slice(),
            ),
            (
                super::compiler_language_contract_bytes().unwrap(),
                include_bytes!("../../../language-contract.lisp").as_slice(),
            ),
            (
                super::compiler_d3_projection_bytes().unwrap(),
                include_bytes!(
                    "../../../knowledge/bija3-l1-l5-structure-projection.json"
                )
                    .as_slice(),
            ),
            (
                super::compiler_d3_authority_bytes().unwrap(),
                include_bytes!("../../../contracts/bija3-l1-l5-ratification.lisp").as_slice(),
            ),
            (
                super::compiler_d4_projection_bytes().unwrap(),
                include_bytes!(
                    "../../../knowledge/d4-bootstrap-compiler-structure-projection.json"
                )
                    .as_slice(),
            ),
            (
                super::compiler_d4_authority_bytes().unwrap(),
                include_bytes!("../../../contracts/d4-bootstrap-ratification.lisp").as_slice(),
            ),
        ];
        for (actual, expected) in sources {
            assert_eq!(actual, expected, "Zig changed compiler source bytes");
            std::str::from_utf8(&actual).expect("compiler source assets are UTF-8");
        }
    }

    #[test]
    fn exact_t5_decode_workspace_uses_a_tight_worst_case_bound() {
        assert_eq!(super::max_t5_decode_record_bytes(1), Some(5));
        assert_eq!(super::max_t5_decode_record_bytes(2), Some(6));
        assert_eq!(super::max_t5_decode_record_bytes(3), Some(10));
        assert_eq!(super::max_t5_decode_record_bytes(100), Some(251));
        assert_eq!(super::max_t5_decode_record_bytes(usize::MAX), None);
    }

    #[test]
    fn exact_t5m_bridge_preserves_domain_width_including_d5_d8_and_d10_plus() {
        use super::{decode_t5m_exact_words, encode_t5m_exact_words, ExactT5MWord};

        // Equal payloads are not interchangeable: D5's 00001 must never be
        // padded into D8's 00000001. Higher D1–24+ words remain opaque here.
        let source = [
            ExactT5MWord::new(5, vec![0, 0, 0, 0, 1]).unwrap(),
            ExactT5MWord::new(8, vec![0, 0, 0, 0, 0, 0, 0, 1]).unwrap(),
            ExactT5MWord::new(10, vec![0, 0, 0, 0, 0, 0, 0, 0, 0, 1]).unwrap(),
            ExactT5MWord::new(24, [vec![0; 23], vec![1]].concat()).unwrap(),
            ExactT5MWord::new(48, [vec![0; 47], vec![1]].concat()).unwrap(),
        ];

        let physical = encode_t5m_exact_words(&source).expect("Zig T5M exact encode");
        let restored = decode_t5m_exact_words(&physical).expect("Zig T5M exact decode");
        assert_eq!(restored, source);
        assert_eq!(restored[0].width(), 5);
        assert_eq!(restored[1].width(), 8);
        assert_ne!(restored[0], restored[1]);
    }

    #[test]
    fn verified_t5m_encode_returns_the_words_it_already_decoded() {
        use super::{decode_t5m_exact_words, encode_t5m_exact_words_and_restore, ExactT5MWord};

        let source = [
            ExactT5MWord::new(3, vec![0, 1, 0]).unwrap(),
            ExactT5MWord::new(24, [vec![0; 23], vec![1]].concat()).unwrap(),
        ];

        let (physical, restored) =
            encode_t5m_exact_words_and_restore(&source).expect("verified Zig T5M roundtrip");
        assert_eq!(restored, source);
        assert_eq!(decode_t5m_exact_words(&physical).unwrap(), restored);
    }

    #[test]
    fn exact_t5m_decoder_preserves_wide_bits_without_inferring_identity() {
        use super::{encode_t5m_exact_words, ExactT5MWord};
        let source = [
            ExactT5MWord::new(10, vec![0, 0, 0, 0, 0, 0, 0, 0, 0, 1]).unwrap(),
            ExactT5MWord::new(24, [vec![0; 23], vec![1]].concat()).unwrap(),
        ];
        let bytes = encode_t5m_exact_words(&source).expect("current T5M bytes");
        let decoded = decode_t5m_exact_words(&bytes).expect("Zig must return numeric exact bits");
        assert!(decoded.iter().any(|word| word.width == 10));
        assert!(decoded.iter().any(|word| word.width == 24));
        assert!(decoded.iter().all(|word| {
            word.bits.len() == word.width && word.bits.iter().all(|&bit| bit <= 1)
        }));
        let error = super::decode_t5m_words(&bytes).expect_err("legacy W1–W9 adapter fails closed");
        assert!(error.contains("точні ширини слів [10, 24]"));
        assert!(error.contains("Ширина не є доменною identity"));
        assert!(error.contains("належність до D1–24+ або викличність не виведено"));
    }

    #[test]
    fn exact_t5m_bridge_roundtrips_variable_width_binary_values() {
        use super::{decode_t5m_exact_words, encode_t5m_exact_words, ExactT5MWord};
        let source = [5usize, 8, 10, 11, 12, 14, 24, 48, 96, 192].map(|width| {
            ExactT5MWord::new(
                width,
                (0..width)
                    .map(|bit| ((bit * 7 + width) % 3 == 0) as u8)
                    .collect(),
            )
                .expect("binary T5M source word")
        });
        let physical = encode_t5m_exact_words(&source).expect("Zig transports exact words");
        assert_eq!(
            decode_t5m_exact_words(&physical).expect("Zig restores exact words"),
            source
        );
    }

    #[test]
    fn coordinate_d10_is_zig_physical_data_not_executable_t5() {
        // The 10 exact zero bits encode as two T5 bytes. This is a
        // coordinate-only Zig witness; Rust never decodes their meaning.
        let d10 = [0x00, 0x00];
        validate_t5_coordinates(&d10).expect("legacy D10 exact physical coordinate");
        validate_t5m(&d10).expect("T5M validates physical bytes, not call admission");

        // T5M is the current .sens wire; the old T5 byte remains an explicit
        // coordinate-only compatibility witness, not the default decoder.
        let d1_t5 = [0xa1];
        validate_t5_coordinates(&d1_t5).expect("legacy T5 D1 coordinate");
        let d1_t5m = encode_t5m_direct(&words("1")).expect("T5M D1 word");
        validate_t5m(&d1_t5m).expect("default T5M carrier");

        // D11=eleven exact zero bits and canonical tail, or bad trits,
        // is never accepted as D10 physical data.
        for invalid in [&[0x00, 0x00, 0x50][..], &[0xff][..], &[][..]] {
            assert!(
                validate_t5_coordinates(invalid).is_err(),
                "invalid D10 coordinate candidate: {invalid:?}"
            );
        }
    }

    #[test]
    fn f3c_no_saving_never_bypasses_zig_t5_physical_validation() {
        // Nine D9 coordinates need >16 canonical T5 bytes, with leading
        // zeros intact. Only Zig decides their physical validity.
        let long_words = words(&["010101000"; 9].join(" "));
        let long_t5 = encode_t5m_direct(&long_words).expect("Zig canonical T5M");
        assert!(long_t5.len() > 16);
        assert!(encode_f3(&long_t5).expect("valid large Zig T5").is_none());

        // Same length, but an out-of-range ternary byte is NEVER benign
        // "F3C not smaller": reject it before the length-based decision.
        let mut corrupt = long_t5.clone();
        corrupt[..3].fill(0xff);
        let failure = encode_f3(&corrupt).expect_err("invalid large T5 must fail closed");
        assert!(failure.contains("Zig physical T5M rejected"));

        // Positive tiny F3C stays on Zig's byte-exact physical path.
        let small = encode_t5m_direct(&words("10 001 00 000 01")).expect("canonical small T5M");
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
                && pack.contains("n < legacy.len()"),
            "encode_f3 must reject overreported / non-smaller F3C lengths before truncate"
        );
        let unpack = src
            .split("pub fn decode_f3(")
            .nth(1)
            .and_then(|s| s.split("#[cfg(test)]").next())
            .expect("decode_f3 route");
        assert!(
            unpack.contains("usize::try_from(len)") && unpack.contains("n <= output.len()"),
            "decode_f3 must reject overreported F3C lengths before truncate"
        );

        // Live golden still round-trips under the stricter bound.
        let small = encode_t5m_direct(&words("10 001 00 000 01")).expect("T5");
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
        let t5 = encode_t5m_direct(&original).expect("Zig physical T5M");
        let e1 = encode_e1_direct(&original).expect("Zig physical E1");
        require_same_exact_words(&original, &decode_t5m_words(&t5).unwrap()).unwrap();
        require_same_exact_words(&original, &decode_e1_words(&e1).unwrap()).unwrap();

        // Both production egress paths must call ONE helper and must not
        // separately rebuild BE3 or use Rust physical encoders.
        let source = include_str!("zig_transport.rs");
        for name in ["encode_t5m_direct", "encode_e1_direct"] {
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
        let physical = encode_t5m_direct(&expected).expect("Zig T5M encode");
        let recovered = decode_t5m_words(&physical).expect("Zig T5M decode");
        require_same_exact_words(&expected, &recovered).unwrap();
        assert_eq!(physical.len(), 4);
    }

    #[test]
    fn e1_egress_reenters_only_zig_and_preserves_exact_domain_words() {
        // W1:1 and W2:01 have the same low payload but different identities.
        // D9 retains nine physical bits including its leading zero.
        let source = words("1 01 001 010101000");
        let frame =
            encode_e1_direct(&source).expect("SENS exact words -> Zig E1 encode -> Zig E1 decode");
        let restored = decode_e1_words(&frame).expect("canonical Zig E1 ingress");
        require_same_exact_words(&source, &restored)
            .expect("byte-for-byte exact width and payload preservation");
        assert_eq!(source.len(), restored.len());
        assert_eq!(
            restored
                .iter()
                .copied()
                .map(sens::BinarySourceWord::width)
                .collect::<Vec<_>>(),
            [1, 2, 3, 9]
        );

        // CRC mutation must fail before any Rust host can admit SENS meaning.
        let mut damaged = frame.clone();
        let last = damaged.len() - 1;
        damaged[last] ^= 1;
        assert!(decode_e1_words(&damaged).is_err());

        // A carrier can be canonical yet represent the WRONG exact words.
        // Fail closed on each domain-width, payload and word-count mismatch.
        assert!(
            require_same_exact_words(&source, &words("01 01 001 010101000"))
                .unwrap_err()
                .contains("expected_width=1")
        );
        assert!(
            require_same_exact_words(&source, &words("0 01 001 010101000"))
                .unwrap_err()
                .contains("index=0")
        );
        assert!(require_same_exact_words(&source, &words("1 01 001"))
            .unwrap_err()
            .contains("word_count"));

        // Scope proof: this production egress has neither Rust E1 codec
        // nor a silent reference fallback after Zig produces bytes.
        let code = include_str!("zig_transport.rs");
        let route = code
            .split("pub fn encode_e1_direct(")
            .nth(1)
            .expect("E1 Zig egress")
            .split("pub fn decode_e1_words(")
            .next()
            .expect("next route");
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
            .unwrap_err()
            .contains("index=0"));
        assert!(require_same_exact_words(&expected, &words("1"))
            .unwrap_err()
            .contains("word_count expected=2 actual=1"));
        assert!(require_same_exact_words(&expected, &words("1 01 0"))
            .unwrap_err()
            .contains("word_count expected=2 actual=3"));
    }
}
